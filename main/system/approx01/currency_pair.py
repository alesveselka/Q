#!/usr/bin/python

import datetime as dt


class CurrencyPair(object):

    def __init__(self, start_data_date, currency_pair_id, code, name, first_data_date):
        self.__start_data_date = start_data_date
        self.__currency_pair_id = currency_pair_id
        self.__code = code
        self.__name = name
        self.__first_data_date = first_data_date
        self.__data = []

    def code(self):
        """
        Return currency pair code

        :return: string representing the pair's code
        """
        return self.__code

    def data(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Return list of data in the range specified by starting and ending dates passed in

        :param start_date:  Date, start fo the data range
        :param end_date:    Date, end of the data range
        :return:            List of data
        """
        return [d for d in self.__data if start_date <= d[0] <= end_date]

    def load_data(self, connection, end_date):
        """
        Load pair's data

        :param connection:  MySQLdb connection instance
        :param end_date:    Last date to fetch data to
        """
        cursor = connection.cursor()
        sql = """
            SELECT price_date, open_price, high_price, low_price, last_price
            FROM currency
            WHERE currency_pair_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s';
        """

        cursor.execute(sql % (
            self.__currency_pair_id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        self.__data = cursor.fetchall()
