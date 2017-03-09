#!/usr/bin/python

from study import *
from enum import Study


class Market(object):

    def __init__(self, connection, start_contract_date, start_data_date, market_id, name, code, data_codes, currency, first_data_date, group):
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
        self.__data = []
        self.__studies = {}

    def __back_adjusted_data(self):
        # TODO 'query' object?
        # TODO move to 'investment_universe'? Do I need the Class?
        cursor = self.__connection.cursor()
        code = ''.join([self.__code, '2']) if 'C' in self.__data_codes else self.__code
        sql = """
            SELECT code, price_date, open_price, high_price, low_price, settle_price
            FROM continuous_back_adjusted
            WHERE market_id = '%s'
            AND code = '%s'
            AND DATE(price_date) >= '%s';
        """

        cursor.execute(sql % (self.__id, code, self.__start_data_date.strftime('%Y-%m-%d')))
        self.__data = cursor.fetchall()

        # print code, len(self.__data)

        # ma = EMA([(d[1], d[5]) for d in self.__data], 50)
        # ma = ATR([(d[1], d[3], d[4], d[5]) for d in self.__data], 50)
        # print self.__code, 'len(ma): %s' % len(ma)
        # for value in ma:
        #     print value

    def update_studies(self):
        self.__back_adjusted_data()

    def data(self, start_date, end_date):
        return [d for d in self.__data if start_date <= d[1] <= end_date]

    def study(self, study_name, window):
        name = '_'.join([study_name, window])
        # TODO refactor 'ifs'
        # TODO remove hard-coded windows
        if name not in self.__studies:
            if study_name == Study.HHLL:
                self.__studies[name] = HHLL([(d[1], d[5]) for d in self.__data], window)
            elif study_name == Study.SMA:
                self.__studies[name] = SMA([(d[1], d[5]) for d in self.__data], window)
            elif study_name == Study.EMA:
                self.__studies[name] = EMA([(d[1], d[5]) for d in self.__data], window)
            elif study_name == Study.ATR:
                self.__studies[name] = ATR([(d[1], d[3], d[4], d[5]) for d in self.__data], window)

        return self.__studies[name]
