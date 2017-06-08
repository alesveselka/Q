#!/usr/bin/python

import datetime as dt
from math import ceil
from study import *
from enum import Study
from enum import Table
from operator import itemgetter
from math import floor, log10


class Market(object):  # TODO rename to Future?

    def __init__(self,
                 start_data_date,
                 market_id,
                 roll_strategy_id,
                 slippage_map,
                 name,
                 code,
                 data_codes,
                 currency,
                 first_data_date,
                 group,
                 tick_value,
                 point_value,
                 margin):

        self.__start_data_date = start_data_date
        self.__id = market_id
        self.__roll_strategy_id = roll_strategy_id
        self.__slippage_map = slippage_map
        self.__name = name
        self.__market_code = code
        self.__instrument_code = ''.join([code, '2']) if 'C' in data_codes else code
        self.__data_codes = data_codes
        self.__currency = currency
        self.__first_data_date = first_data_date
        self.__group = group
        self.__tick_value = tick_value
        self.__point_value = point_value
        self.__margin = margin
        self.__margin_multiple = 0.0
        self.__adjusted_data = []
        self.__contracts = []
        self.__contract_rolls = []
        self.__studies = {}
        self.__first_study_date = dt.date(9999, 12, 31)

    def id(self):
        return self.__id

    def code(self):
        return self.__instrument_code

    def currency(self):
        return self.__currency

    def point_value(self):
        return self.__point_value

    def first_study_date(self):
        return self.__first_study_date

    def data(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Filter and return data that fall in between dates passed in

        :param start_date:  Date of first date of the data range
        :param end_date:    Date of last date of the data range
        :return:            List of market data records
        """
        return [d for d in self.__adjusted_data if start_date <= d[Table.Market.PRICE_DATE] <= end_date]

    def has_data(self, date):
        """
        Check if the market has data for date specified

        :param date:    date to check data for
        :return:
        """
        return self.data(end_date=date)[-1][Table.Market.PRICE_DATE] == date

    def margin(self, date):
        """
        Calculates margin estimate

        :param date:    Date on which to estimate the margin
        :return:        Number representing margin in account-base-currency
        """
        return Decimal(ceil(self.__margin_multiple * self.study(Study.ATR_SHORT, date)[-1][Table.Study.VALUE]))

    def slippage(self, date, quantity):
        """
        Calculates and returns 'slippage' in points
        (At minimum 1 tick)

        :param date:        date on which to calculate the slippage
        :param quantity:    number of contracts to open
        :return:            Number representing slippage in market points
        """
        atr = self.study(Study.ATR_SHORT, date)[-1][Table.Study.VALUE]
        volume = self.study(Study.VOL_SHORT, date)[-1][Table.Study.VALUE]
        atr_multiple = [s for s in self.__slippage_map if s['min'] <= volume < s['max']][0].get('atr')
        quantity_factor = Decimal(2 ** floor(log10(quantity)))
        slippage_value = Decimal(atr_multiple) * atr
        result = (Decimal(ceil(slippage_value / self.__tick_value)) * self.__tick_value) / self.__point_value
        return result * quantity_factor

    def contract(self, date):
        """
        Find and return contract to be in on the date passed in
        
        :param date:    date of the contract
        :return:        string representing the contract delivery
        """
        contract_rolls = [r for r in zip(self.__contract_rolls, self.__contract_rolls[1:])
                         if r[0][Table.ContractRoll.DATE] < date <= r[1][Table.ContractRoll.DATE]]
        contract_roll = contract_rolls[0][0] if len(contract_rolls) == 1 else self.__contract_rolls[-1]

        return contract_roll[Table.ContractRoll.ROLL_IN_CONTRACT]

    def contract_roll(self, current_contract):
        """
        Find and return contract roll based on current contract passed in
        
        :param current_contract:    string representing current contract
        :return:                    tuple(date, gap, roll-out-contract, roll-in-contract)
        """
        return [r for r in self.__contract_rolls if r[Table.ContractRoll.ROLL_OUT_CONTRACT] == current_contract][0]

    def study(self, study_name, date=dt.date(9999, 12, 31)):
        """
        Return data of the study to the date passed in

        :param study_name:  Name of the study which data to return
        :param date:        last date of data required
        :return:            List of tuples - records of study specified
        """
        return [s for s in self.__studies[study_name] if s[Table.Study.DATE] <= date]

    def calculate_studies(self, study_parameters):
        """
        Calculates and saves studies based on parameters passed in

        :param study_parameters:    List of dictionaries with parameters for each study to calculate
        """
        if len(self.__adjusted_data):
            for params in study_parameters:
                self.__studies[params['name']] = params['study'](
                    [tuple(map(lambda c: d[c], params['columns'])) for d in self.__adjusted_data],
                    params['window']
                )

            self.__first_study_date = max([self.__studies[k][0][0] for k in self.__studies.keys()])

            margin = self.__margin if self.__margin else self.__adjusted_data[-1][Table.Market.SETTLE_PRICE] * self.__point_value * 0.1
            self.__margin_multiple = margin / self.study(Study.ATR_SHORT)[-1][Table.Study.VALUE]

    def load_data(self, connection, end_date):
        """
        Load market's data

        :param connection:  MySQLdb connection instance
        :param end_date:    Last date to fetch data to
        """
        cursor = connection.cursor()
        continuous_query = """
            SELECT %s
            FROM %s
            WHERE market_id = '%s'
            AND code = '%s' 
            AND roll_strategy_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s';
        """
        cursor.execute(continuous_query % (
            self.__column_names(),
            'continuous_adjusted',
            self.__id,
            self.__instrument_code,
            self.__roll_strategy_id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        self.__adjusted_data = cursor.fetchall()

        contracts_query = """
            SELECT %s
            FROM %s
            WHERE market_id = '%s'
            AND code = '%s' 
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s';
        """
        cursor.execute(contracts_query % (
            self.__column_names() + ', last_trading_day',
            'contract',
            self.__id,
            self.__instrument_code,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        self.__contracts = cursor.fetchall()

        roll_query = """
            SELECT date, gap, roll_out_contract, roll_in_contract
            FROM contract_roll
            WHERE market_id = '%s'
            AND roll_strategy_id = '%s'
            ORDER BY date;
        """
        cursor.execute(roll_query % (self.__id, self.__roll_strategy_id))
        contract_rolls = cursor.fetchall()
        self.__contract_rolls = contract_rolls if len(contract_rolls) else [(None, 0, None, None)]

        return True

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
