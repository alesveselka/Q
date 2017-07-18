#!/usr/bin/python

import datetime as dt
from enum import Table
from enum import RollSchedule
from collections import defaultdict
from series.market_series import MarketSeries


class CustomSeries(MarketSeries):

    def __init__(self, start_data_date, study_parameters, roll_strategy):
        super(CustomSeries, self).__init__(start_data_date, study_parameters, roll_strategy)

        self.__contracts = defaultdict(list)
        self.__roll_schedule = []
        self.__scheduled_rolls = []
        self.__rolls = []
        self.__gaps = 0.0

    def contract(self, date):
        """
        Return contract on the date passed in
        
        :param date:    date by which find the contract
        :return:        contract symbol code
        """
        return self._prices[self._price_indexes[date]][Table.Market.CODE]

    def rolls(self):
        """
        Return contract rolls
        
        :return:    list of tuples(date, gap, roll-out-contract, roll-in-contract)
        """
        return self.__rolls

    def update_data(self, date):
        """
        Update dynamic data
        
        :param date:    date of the data update
        """
        scheduled_contract = self.__scheduled_roll(date)[Table.ContractRoll.ROLL_IN_CONTRACT]
        contract_data = [d for d in self.__contracts[scheduled_contract] if d[Table.Market.PRICE_DATE] == date]
        if len(contract_data):
            self._prices.append(tuple(i[1] if i[0] else i[1][-5:] for i in enumerate(contract_data[-1])))
            index = len(self._prices) - 1
            self._price_indexes[date] = index

            if self._prices[index][Table.Market.CODE] != self._prices[index-1][Table.Market.CODE]:
                previous_contract = self._prices[index-1][Table.Market.CODE]
                previous_data = [d for d in self.__contracts[previous_contract] if d[Table.Market.PRICE_DATE] <= date][-1]
                gap = self._prices[index][Table.Market.SETTLE_PRICE] - previous_data[Table.Market.SETTLE_PRICE]
                self.__rolls.append((date, gap, previous_contract, self._prices[index][Table.Market.CODE]))
                self.__contracts.pop(previous_contract, None)
                self.__gaps = sum(roll[1] for roll in self.__rolls)

            self._prices[index] = tuple(d - self.__gaps if isinstance(d, float) else d for d in self._prices[index])

    def load(self, connection, end_date, delivery_months, market_id, market_code, roll_strategy_id):
        """
        Load market's data

        :param connection:          MySQLdb connection instance
        :param end_date:            Last date to fetch data to
        :param delivery_months:     list of delivery months [(code, short-month-name)]
        :param market_id:           ID of the series market
        :param market_code:         code symbol of the series market
        :param roll_strategy_id:    ID of the series roll strategy
        """
        super(CustomSeries, self).load(connection, end_date, delivery_months, market_id, market_code, roll_strategy_id)

        # TODO use connection pool?
        cursor = connection.cursor()
        contracts_query = """
            SELECT %s
            FROM contract
            WHERE market_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
        cursor.execute(contracts_query % (
            self._column_names() + ', last_trading_day',
            market_id,
            self._start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        for contract in [c for c in cursor.fetchall() if market_code == c[Table.Market.CODE][:-5]]:
            self.__contracts[contract[Table.Market.CODE][-5:].upper()].append(contract)

        roll_schedule_query = """
            SELECT roll_out_month, roll_in_month, month, day
            FROM standard_roll_schedule
            WHERE market_id = '%s';
        """
        cursor.execute(roll_schedule_query % market_id)
        self.__roll_schedule = cursor.fetchall()

        self.__schedule_rolls(delivery_months)

        return True

    def margin(self, end_date, point_value):
        """
        Return calculated margin based on price and point value at the date passed in
        
        :param end_date:    date to calculate margin on
        :param point_value: point value of the market instrument
        :return:            number representing margin
        """
        contract = self.__scheduled_roll(end_date)[Table.ContractRoll.ROLL_IN_CONTRACT]
        contract_data = [d for d in self.__contracts[contract] if d[Table.Market.PRICE_DATE] <= end_date]
        price = contract_data[-1][Table.Market.SETTLE_PRICE] if len(contract_data) else None
        return price * point_value * 0.1

    def __schedule_rolls(self, delivery_months):
        """
        Schedule rolls based on contracts available and roll schedule
        
        :param delivery_months:     list of delivery months
        """
        scheduled_months = [r[RollSchedule.ROLL_OUT_MONTH] for r in self.__roll_schedule]
        scheduled_codes = [k for k in delivery_months.keys() if delivery_months[k][1] in scheduled_months]
        contract_keys = sorted(self.__contracts.keys())
        contract_codes = [c for c in [k for k in contract_keys] if c[-1] in scheduled_codes]

        self.__scheduled_rolls = [(self.__scheduled_roll_date(r[0], delivery_months), 0, r[0], r[1])
                                  for r in zip(contract_codes, contract_codes[1:])]

        self.__rolls.append(self.__scheduled_roll(self._start_data_date))

        for key in contract_keys:
            key not in contract_codes and self.__contracts.pop(key, None)

    def __scheduled_roll(self, date):
        """
        Return scheduled roll for the date passed in
        
        :param date:    date of the scheduled roll
        :return:        scheduled roll (date, gap, roll-out-contract, roll-in-contract)
        """
        contract_rolls = [r for r in zip(self.__scheduled_rolls, self.__scheduled_rolls[1:])
                          if r[0][Table.ContractRoll.DATE] <= date < r[1][Table.ContractRoll.DATE]]
        contract_roll = contract_rolls[0][0] if len(contract_rolls) == 1 \
            else (self.__scheduled_rolls[0] if date < self.__scheduled_rolls[0][Table.ContractRoll.DATE] else self.__scheduled_rolls[-1])

        return contract_roll

    def __scheduled_roll_date(self, contract, delivery_months):
        """
        Return market's next scheduled roll date based on contract passed in
        
        :param contract:        contract which roll date to find
        :param delivery_months: list of delivery months [(code, short-month-name)]
        :return:                date of scheduled roll
        """
        contract_year = int(contract[:4])
        contract_month_code = contract[-1]
        contract_month_index, contract_month = delivery_months[contract_month_code]

        roll_schedule = [r for r in self.__roll_schedule if r[RollSchedule.ROLL_OUT_MONTH] == contract_month][0]

        roll_month_index = [delivery_months[k][0] for k in delivery_months.keys() if delivery_months[k][1] == roll_schedule[RollSchedule.MONTH]][0]
        roll_year = contract_year if contract_month_index - roll_month_index > -1 else contract_year - 1
        return dt.date(roll_year, roll_month_index, int(roll_schedule[RollSchedule.DAY]))
