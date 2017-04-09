#!/usr/bin/python

import datetime as dt
from math import ceil
from study import *


class Market(object):  # TODO rename to Future?

    def __init__(self,
                 start_data_date,
                 market_id,
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
        self.__name = name
        self.__code = code
        self.__data_codes = data_codes
        self.__currency = currency
        self.__first_data_date = first_data_date
        self.__group = group
        self.__tick_value = tick_value
        self.__point_value = point_value
        self.__margin = margin if margin else Decimal(0.1)
        self.__margin_multiple = 0.0
        self.__data = []
        self.__studies = {}

    def load_data(self, connection, end_date):
        """
        Load market's data

        :param connection:  MySQLdb connection instance
        :param end_date:    Last date to fetch data to
        """
        cursor = connection.cursor()
        code = ''.join([self.__code, '2']) if 'C' in self.__data_codes else self.__code
        sql = """
            SELECT code, price_date, open_price, high_price, low_price, settle_price, volume
            FROM continuous_back_adjusted
            WHERE market_id = '%s'
            AND code = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s';
        """

        cursor.execute(sql % (
            self.__id,
            code,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        self.__data = cursor.fetchall()

        # TODO update more realistically - include actual ATR?
        self.__margin_multiple = (self.__margin / (self.__data[-1][5] * self.__point_value)) \
            if len(self.__data) \
            else Decimal(0.1)

        return True

    def code(self):
        return self.__code

    def currency(self):
        return self.__currency

    def point_value(self):
        return self.__point_value

    def data(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Filter and return data that fall in between dates passed in

        :param start_date:  Date of first date of the data range
        :param end_date:    Date of last date of the data range
        :return:            List of market data records
        """
        return [d for d in self.__data if start_date <= d[1] <= end_date]

    def has_data(self, date):
        """
        Check if the market has data for date specified

        :param date:    date to check data for
        :return:
        """
        return self.data(end_date=date)[-1][1] == date

    def margin(self, price):
        """
        Calculates margin estimate

        :param price:   Market price for margin calculation
        :return:        Number representing margin in account-base-currency
        """
        return ceil(price * self.__point_value * self.__margin_multiple)

    def slippage(self, average_volume, atr):
        """
        Calculates and returns 'slippage' in points
        (At minimum 1 tick)

        :param average_volume:  Average volume for slippage estimation
        :param atr:             ATR of Settlement price
        :return:                Number representing slippage in market points
        """
        # TODO remove hard-coded slippage-map (pass in as dependency)
        # TODO factor in quantity?
        slippage_atr = filter(lambda s: s.get('min') <= average_volume < s.get('max'), [
            {'atr': 2, 'min': 0, 'max': 100},
            {'atr': 1, 'min': 100, 'max': 1000},
            {'atr': 0.25, 'min': 1000, 'max': 10000},
            {'atr': 0.1, 'min': 10000, 'max': 50000},
            {'atr': 0.05, 'min': 50000, 'max': 200000},
            {'atr': 0.01, 'min': 200000, 'max': 1e9}
        ])[0].get('atr')
        slippage_value = Decimal(slippage_atr) * atr * self.__point_value
        return (Decimal(ceil(slippage_value / self.__tick_value)) * self.__tick_value) / self.__point_value

    def study(self, study_name, date=dt.date(9999, 12, 31)):
        """
        Return data of the study to the date passed in

        :param study_name:  Name of the study which data to return
        :param date:        last date of data required
        :return:            List of tuples - records of study specified
        """
        return [s for s in self.__studies[study_name] if s[0] <= date]

    def calculate_studies(self, study_parameters):
        """
        Calculates and saves studies based on parameters passed in

        :param study_parameters:    List of dictionaries with parameters for each study to calculate
        """
        if len(self.__data):
            for params in study_parameters:
                self.__studies[params['name']] = params['study'](
                    [tuple(map(lambda c: d[c], params['columns'])) for d in self.__data],
                    params['window']
                )
