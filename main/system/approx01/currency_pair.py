#!/usr/bin/python

import datetime as dt


class CurrencyPair(object):

    def __init__(self, connection, start_data_date, currency_pair_id, code, name, first_data_date):
        self.__connection = connection
        self.__start_data_date = start_data_date
        self.__currency_pair_id = currency_pair_id
        self.__code = code
        self.__name = name
        self.__first_data_date = first_data_date
        self.__data = []

    def load_data(self):
        cursor = self.__connection.cursor()
        sql = """
            SELECT price_date, open_price, high_price, low_price, last_price
            FROM currency
            WHERE currency_pair_id = '%s'
            AND DATE(price_date) >= '%s';
        """

        cursor.execute(sql % (self.__currency_pair_id, self.__start_data_date.strftime('%Y-%m-%d')))
        self.__data = cursor.fetchall()

    def code(self):
        return self.__code

    def data(self, start_date=dt.date(1970, 1, 1), end_date=dt.date(2100, 1, 1)):
        """
        Return list of data in the range specified by starting and ending dates passed in

        :param start_date:  Date, start fo the data range
        :param end_date:    Date, end of the data range
        :return:            List of data
        """
        return [d for d in self.__data if start_date <= d[0] <= end_date]
