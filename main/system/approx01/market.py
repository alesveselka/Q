#!/usr/bin/python

import time
from math import ceil
from math import floor
from study import *
from enum import Study


class Market(object):

    def __init__(self,
                 connection,
                 start_contract_date,
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

        self.__connection = connection
        self.__start_contract_date = start_contract_date
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
        self.__margin = margin
        self.__data = []
        self.__studies = {}

    def __back_adjusted_data(self):
        # TODO 'query' object?
        # TODO move to 'investment_universe'? Do I need the Class?
        cursor = self.__connection.cursor()
        code = ''.join([self.__code, '2']) if 'C' in self.__data_codes else self.__code
        # TODO also fetch 'volume' for slippage estimation ...
        sql = """
            SELECT code, price_date, open_price, high_price, low_price, settle_price, volume
            FROM continuous_back_adjusted
            WHERE market_id = '%s'
            AND code = '%s'
            AND DATE(price_date) >= '%s';
        """

        cursor.execute(sql % (self.__id, code, self.__start_data_date.strftime('%Y-%m-%d')))
        self.__data = cursor.fetchall()

    def update_studies(self):
        self.__back_adjusted_data()

        # self.slippage(
        #     SMA([(d[1], d[6]) for d in self.__data], 50)[-1][1],
        #     ATR([(d[1], d[3], d[4], d[5]) for d in self.__data], 50)[-1][1]
        # )

    def code(self):
        return self.__code

    def currency(self):
        return self.__currency

    def point_value(self):
        return self.__point_value

    def data(self, start_date, end_date):
        """
        Filter and return data that fall in between dates passed in

        :param start_date:  Date of first date of the data range
        :param end_date:    Date of last date of the data range
        :return:            List of market data records
        """
        return [d for d in self.__data if start_date <= d[1] <= end_date]

    def margin(self, price):
        """
        Calculates margin estimate

        :param price:   Market price for margin calculation
        :return:        Number representing margin in account-base-currency
        """
        # TODO convert non-base-currency point_value!
        margin_multiple = (self.__margin if self.__margin else Decimal(0.1)) / (price * self.__point_value)
        return ceil(price * self.__point_value * margin_multiple)

    def slippage(self, average_volume, atr):
        """
        Calculates and returns 'slippage' in points
        (At minimum 1 tick)

        :param average_volume:  Average volume for slippage estimation
        :param atr:             ATR of Settlement price
        :return:                Number representing slippage in market points
        """
        # TODO remove hard-coded slippage-map (pass in as dependency)
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

    def study(self, study_name, data, window):
        name = '_'.join([study_name, str(window)])
        # TODO refactor 'ifs'
        # TODO remove hard-coded windows
        # TODO the studies don't have to be here - there is no dependency on local vars ...
        if name not in self.__studies:
            if study_name == Study.HHLL:
                # self.__studies[name] = HHLL([(d[1], d[5]) for d in data], window)
                return HHLL([(d[1], d[5]) for d in data], window)
            elif study_name == Study.SMA:
                # self.__studies[name] = SMA([(d[1], d[5]) for d in data], window)
                return SMA([(d[1], d[5]) for d in data], window)
            elif study_name == Study.EMA:
                # self.__studies[name] = EMA([(d[1], d[5]) for d in data], window)
                return EMA([(d[1], d[5]) for d in data], window)
            elif study_name == Study.ATR:
                # self.__studies[name] = ATR([(d[1], d[3], d[4], d[5]) for d in data], window)
                return ATR([(d[1], d[3], d[4], d[5]) for d in data], window)

        # return self.__studies[name]
