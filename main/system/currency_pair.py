#!/usr/bin/python

import datetime as dt
from enum import Table
from operator import itemgetter


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
        return [d for d in self.__data if start_date <= d[Table.CurrencyPair.PRICE_DATE] <= end_date]

    def rate(self, date=dt.date(9999, 12, 31)):
        """
        Find and return rate on date specified

        :param date:    date to return rate on
        :return:        Number representing the rate on the date
        """
        pair_data = self.data(end_date=date)
        return pair_data[-1][Table.CurrencyPair.LAST_PRICE] if len(pair_data) else 1.0

    def load_data(self, connection, end_date):
        """
        Load pair's data

        :param connection:  MySQLdb connection instance
        :param end_date:    Last date to fetch data to
        """
        cursor = connection.cursor()
        sql = """
            SELECT %s
            FROM currency
            WHERE currency_pair_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s';
        """

        cursor.execute(sql % (
            self.__column_names(),
            self.__currency_pair_id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        self.__data = cursor.fetchall()

    def __column_names(self):
        """
        Construct and return column names sorted by their index in ENUM

        :return:    string
        """
        columns = {
            'price_date': Table.CurrencyPair.PRICE_DATE,
            'open_price': Table.CurrencyPair.OPEN_PRICE,
            'high_price': Table.CurrencyPair.HIGH_PRICE,
            'low_price': Table.CurrencyPair.LOW_PRICE,
            'last_price': Table.CurrencyPair.LAST_PRICE
        }
        return ', '.join([i[0] for i in sorted(columns.items(), key=itemgetter(1))])
