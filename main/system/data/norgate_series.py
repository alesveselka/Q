#!/usr/bin/python

import datetime as dt
from enum import Table
from enum import RollSchedule
from operator import itemgetter
from collections import deque
from collections import defaultdict
from data.market_series import MarketSeries


class NorgateSeries(MarketSeries):

    def __init__(self, start_data_date, study_parameters):
        super(NorgateSeries, self).__init__(start_data_date, study_parameters)
        
        # self.__roll_strategy_id = roll_strategy_id
        self.__adjusted_data = []
        self.__data_indexes = {}

        self.__prices = []
        self.__price_indexes = {}

        self.__contracts = defaultdict(list)
        self.__roll_schedule = []
        self.__scheduled_rolls = []
        self.__rolls = []

        self.__studies = defaultdict(list)
        self.__study_data = {}
        self.__study_indexes = defaultdict(dict)

        self.__first_study_date = dt.date(9999, 12, 31)
        self.__has_study_data = False

    def data(self, date):
        """
        Return market data at the date passed in

        :param date:    date of the required data
        :return:        tuple representing one day record
        """
        # index = self.__data_indexes[date] if date in self.__data_indexes else None
        # return (self.__adjusted_data[index], self.__adjusted_data[index-1]) if index else (None, None)
        index = self.__price_indexes[date] if date in self.__price_indexes else None
        return (self.__prices[index], self.__prices[index-1]) if index else (None, None)

    def data_range(self, start_date, end_date):
        """
        Return data between the start and end date passed in
        
        :param start_date:  start date of the data
        :param end_date:    end date of the data
        :return:            list of data
        """
        return [d for d in self.__prices if start_date <= d[Table.Market.PRICE_DATE] <= end_date]

    # def contract_roll(self, current_contract):
    #     """
    #     Find and return contract roll based on current contract passed in
    #
    #     :param current_contract:    string representing current contract
    #     :return:                    tuple(date, gap, roll-out-contract, roll-in-contract)
    #     """
    #     rolls = self.__contract_rolls if len(self.__contract_rolls) else self.__scheduled_rolls
    #     return [r for r in rolls if r[Table.ContractRoll.ROLL_OUT_CONTRACT] == current_contract][0]
    #
    # def yield_curve(self, date):
    #     """
    #     Calculate yield curve relative to the date passed in
    #
    #     :param date:    date to which relate the yield curve
    #     :return:        list of tuples(code, price, volume, yield, relative-price-difference))
    #     """
    #     current_contract_code = self.__contract(date)
    #     current_contract = [c for c in self.__contracts[current_contract_code] if c[Table.Market.PRICE_DATE] <= date][-1]
    #     contract_codes = [k for k in sorted(self.__contracts.keys()) if k > current_contract_code]
    #     previous_price = current_contract[Table.Market.SETTLE_PRICE] if current_contract else 0
    #     curve = [(
    #         current_contract_code,
    #         current_contract[Table.Market.SETTLE_PRICE],
    #         current_contract[Table.Market.VOLUME],
    #         None,
    #         None,
    #         (current_contract[Table.Market.LAST_TRADING_DAY] - date).days
    #     )]
    #
    #     # TODO normalize with ATR
    #     # TODO also calculate average volatility of each contract
    #     for code in contract_codes:
    #         next_contract_data = [c for c in self.__contracts[code] if c[Table.Market.PRICE_DATE] <= date]
    #         if len(next_contract_data):
    #             next_contract = next_contract_data[-1]
    #             days = (next_contract[Table.Market.LAST_TRADING_DAY] - date).days
    #             price = next_contract[Table.Market.SETTLE_PRICE]
    #             implied_yield = (price / current_contract[Table.Market.SETTLE_PRICE]) ** (365. / days) - 1
    #             price_difference = price - previous_price
    #             previous_price = price
    #             curve.append((code, price, next_contract[Table.Market.VOLUME], implied_yield, price_difference, days))
    #
    #     return curve

    def __contract(self, date):
        """
        Find and return contract to be in on the date passed in
        
        :param date:    date of the contract
        :return:        string representing the contract delivery
        """
        contract_rolls = [r for r in zip(self.__scheduled_rolls, self.__scheduled_rolls[1:])
                          if r[0][Table.ContractRoll.DATE] <= date < r[1][Table.ContractRoll.DATE]]
        contract_roll = contract_rolls[0][0] if len(contract_rolls) == 1 \
            else (self.__scheduled_rolls[0] if date < self.__scheduled_rolls[0][Table.ContractRoll.DATE] else self.__scheduled_rolls[-1])

        return contract_roll[Table.ContractRoll.ROLL_IN_CONTRACT]

    def study(self, study_name, date=None):
        """
        Return data of the study to the date passed in

        :param study_name:  Name of the study which data to return
        :param date:        last date of data required
        :return:            List of tuples - records of study specified
        """
        index = (self.__study_indexes[study_name][date] if date in self.__study_indexes[study_name] else None) \
            if date else len(self.__study_indexes[study_name]) - 1
        return self.__studies[study_name][index] if index > -1 else None

    def study_range(self, study_name, start_date, end_date):
        """
        Return study data within range of the dates passed in
        
        :param study_name:  name of the study to return
        :param start_date:  start date of the data range
        :param end_date:    end date of the data range
        :return:            list of tuple(date, value, value_2)
        """
        return [s for s in self.__studies[study_name] if start_date <= s[Table.Study.DATE] <= end_date]

    def update_data(self, date):
        """
        Update dynamic data
        
        :param date:    date of the data update
        """
        # TODO not necessary if all markets have data - filter universe based on first contract date
        # TODO don't have to call every single time - just before rolling
        contract = self.__contract(date) if len(self.__scheduled_rolls) else None
        contract_data = self.__contracts[contract] if contract else []
        # TODO cache contract data
        contract_data = [d for d in contract_data if d[Table.Market.PRICE_DATE] == date]
        if len(contract_data):
            self.__prices.append(contract_data[-1])
            index = len(self.__prices) - 1
            self.__price_indexes[date] = index

            if self.__prices[index][Table.Market.CODE] != self.__prices[index-1][Table.Market.CODE]:
                previous_contract = self.__contracts[self.__prices[index-1][Table.Market.CODE][-5:]]
                previous_data = [d for d in previous_contract if d[Table.Market.PRICE_DATE] <= date][-1]
                gap = self.__prices[index][Table.Market.SETTLE_PRICE] - previous_data[Table.Market.SETTLE_PRICE]
                self.__rolls.append((date, gap, self.__prices[index-1][Table.Market.CODE], self.__prices[index][Table.Market.CODE]))

            if len(self.__rolls):
                gap = sum(roll[1] for roll in self.__rolls)
                self.__prices[index] = tuple(d - gap if isinstance(d, float) else d for d in contract_data[-1])

    def update_studies(self, date):
        """
        Update dynamic studies
        
        :param date:                date of the update
        """
        if date in self.__price_indexes:
            index = self.__price_indexes[date]
            market_data = self.__prices[index]
            settle_price = market_data[Table.Market.SETTLE_PRICE]
            previous_settle = self.__prices[index-1][Table.Market.SETTLE_PRICE] if index else settle_price
            volume = market_data[Table.Market.VOLUME]
            tr = max(market_data[Table.Market.HIGH_PRICE], previous_settle) - min(market_data[Table.Market.LOW_PRICE], previous_settle)
            study_data_keys = set('%s:%s' % (p['columns'][-1] if len(p['columns']) == 2 else 'tr', p['window']) for p in self.__study_parameters)
            l = locals()
            for key in study_data_keys:
                column, window = key.split(':')
                self.__study_data['%s_%s' % (column, window)].append(l[column])

            has_study = []
            for params in self.__study_parameters:
                window = params['window']
                study_type = params['study']
                study_name = params['name']
                study = self.__studies[study_name]
                data_columns = params['columns'][1:]
                column = data_columns[-1] if len(data_columns) == 1 else 'tr'
                study_data = self.__study_data['%s_%s' % (column, window)]

                if study_type == 'SMA':
                    study.append((date, sum(study_data) / len(study_data)))

                if study_type == 'EMA' or study_type == 'ATR':
                    c = 2.0 / (window + 1)
                    ma = study[-1][1] if len(study) else (sum(study_data) / len(study_data))
                    study.append((date, (c * l[column]) + (1 - c) * ma))

                if study_type == 'HHLL':
                    study.append((date, max(study_data), min(study_data)))

                self.__study_indexes[study_name][date] = len(study) - 1

                has_study.append(len(study) >= window)

            self.__has_study_data = all(has_study)

    def has_study_data(self):
        """
        Returns flag indicating if the market has studies data
        
        :return:    boolean
        """
        return self.__has_study_data

    def load(self, connection, end_date, delivery_months, market_id, market_code):
        """
        Load market's data

        :param connection:          MySQLdb connection instance
        :param end_date:            Last date to fetch data to
        :param delivery_months:     list of delivery months [(code, short-month-name)]
        """
        # TODO use connection pool?
        cursor = connection.cursor()
        continuous_query = """
            SELECT %s
            FROM %s
            WHERE market_id = '%s'
            AND code = '%s'
            AND roll_strategy_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
        cursor.execute(continuous_query % (
            self.__column_names(),
            'continuous_adjusted',
            market_id,
            market_code,
            2,  #self.__roll_strategy_id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        # TODO I can make a generator and retrieve the data when needed
        self.__adjusted_data = cursor.fetchall()
        self.__data_indexes = {i[1][Table.Market.PRICE_DATE]: i[0] for i in enumerate(self.__adjusted_data)}

        contracts_query = """
            SELECT %s
            FROM %s
            WHERE market_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
        cursor.execute(contracts_query % (
            self.__column_names() + ', last_trading_day',
            'contract',
            market_id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        for c in cursor.fetchall():
            self.__contracts[c[Table.Market.CODE][-5:].upper()].append(c)

        roll_schedule_query = """
            SELECT roll_out_month, roll_in_month, month, day
            FROM standard_roll_schedule
            WHERE market_id = '%s'
            AND name = 'norgate';
        """
        cursor.execute(roll_schedule_query % market_id)
        self.__roll_schedule = cursor.fetchall()

        contract_codes = self.__scheduled_codes([k for k in sorted(self.__contracts.keys())], delivery_months)
        self.__scheduled_rolls = [(self.__scheduled_roll_date(r[0], delivery_months), 0, r[0], r[1])
                                  for r in zip(contract_codes, contract_codes[1:])]

        # for roll in self.__scheduled_rolls:
        #     print roll

        study_data_keys = set('%s:%s' % (p['columns'][-1] if len(p['columns']) == 2 else 'tr', p['window']) for p in self.__study_parameters)
        for key in study_data_keys:
            column, window = key.split(':')
            self.__study_data['%s_%s' % (column, window)] = deque([], int(window))

        # if self.__margin == 0:
        #     contract = self.__contract(end_date)
        #     contract_data = [d for d in self.__contracts[contract] if d[Table.Market.PRICE_DATE] <= end_date]
        #     price = contract_data[-1][Table.Market.SETTLE_PRICE] if len(contract_data) else None
        #     self.__margin = price * self.__point_value * 0.1

        return True

    # TODO move elsewhere
    # TODO actually implement margin multiplier, but with contract data?
    def margin(self, end_date, point_value):
        contract = self.__contract(end_date)
        contract_data = [d for d in self.__contracts[contract] if d[Table.Market.PRICE_DATE] <= end_date]
        price = contract_data[-1][Table.Market.SETTLE_PRICE] if len(contract_data) else None
        return price * point_value * 0.1

    def __scheduled_codes(self, contract_codes, delivery_months):
        """
        Filter out contract codes which months are not included in scheduled rolls
        
        :param contract_codes:  list of contract codes
        :param delivery_months: list of delivery months [(code, short-month-name)]
        :return:                list of contract codes
        """
        scheduled_months = [r[RollSchedule.ROLL_OUT_MONTH] for r in self.__roll_schedule]
        scheduled_codes = [k for k in delivery_months.keys() if delivery_months[k][1] in scheduled_months]
        return [c for c in contract_codes if c[-1] in scheduled_codes]

    def __scheduled_roll_date(self, contract, delivery_months):
        """
        Return market's next scheduled roll date based on contract passed in
        
        :param contract:        contract which roll date to find
        :param delivery_months: list of delivery months [(code, short-month-name)]
        :return:                date of scheduled roll
        """
        # months = [m for m in calendar.month_abbr]

        contract_year = int(contract[:4])
        contract_month_code = contract[-1]
        # contract_month_index = reduce(lambda i, d: i + 1 if d[0] <= contract_month_code else i, delivery_months, 0)
        contract_month_index = delivery_months[contract_month_code][0]
        contract_month = delivery_months[contract_month_code][1]
        # contract_month = months[contract_month_index]

        roll_schedule = [r for r in self.__roll_schedule if r[RollSchedule.ROLL_OUT_MONTH] == contract_month][0]

        # roll_month_index = [i[0] for i in enumerate(months) if i[1] == roll_schedule[RollSchedule.MONTH]][0]
        roll_month_index = [delivery_months[k][0] for k in delivery_months.keys() if delivery_months[k][1] == roll_schedule[RollSchedule.MONTH]][0]
        roll_year = contract_year if contract_month_index - roll_month_index > -1 else contract_year - 1
        return dt.date(roll_year, roll_month_index, int(roll_schedule[RollSchedule.DAY]))

    def __column_names(self):
        """
        Construct and return column names sorted by their index in ENUM

        :return:    string
        """
        # TODO External 'Entity'?
        columns = {
            'code': Table.Market.CODE,
            'price_date': Table.Market.PRICE_DATE,
            'open_price': Table.Market.OPEN_PRICE,
            'high_price': Table.Market.HIGH_PRICE,
            'low_price': Table.Market.LOW_PRICE,
            'settle_price': Table.Market.SETTLE_PRICE,
            'volume': Table.Market.VOLUME
        }
        return ', '.join([i[0] for i in sorted(columns.items(), key=itemgetter(1))])
