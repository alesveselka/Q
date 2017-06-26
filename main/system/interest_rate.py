#!/usr/bin/python

import datetime as dt
from enum import Table
from operator import itemgetter


class InterestRate(object):

    def __init__(self, start_data_date, currency_id, currency_code):
        self.__start_data_date = start_data_date
        self.__currency_id = currency_id
        self.__currency_code = currency_code
        self.__data = []

    def code(self):
        """
        Return currency symbol

        :return:    String - symbol of the currency
        """
        return self.__currency_code

    def load_data(self, connection, end_date):
        """
        Load data from DB

        :param connection:  MySQLdb connection
        :param end_date:    Last date to fetch data to
        """
        cursor = connection.cursor()
        sql = """
            SELECT %s
            FROM interest_rate
            WHERE currency_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date ASC;
        """

        cursor.execute(sql % (
            self.__column_names(),
            self.__currency_id,
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
            'price_date': Table.InterestRate.PRICE_DATE,
            'immediate_rate': Table.InterestRate.IMMEDIATE_RATE,
            'three_months_rate': Table.InterestRate.THREE_MONTHS_RATE
        }
        return ', '.join([i[0] for i in sorted(columns.items(), key=itemgetter(1))])

    def data(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Return list of data in the range specified by starting and ending dates passed in

        :param start_date:  Date, start fo the data range
        :param end_date:    Date, end of the data range
        :return:            List of data
        """
        return [d for d in self.__data if start_date <= d[Table.InterestRate.PRICE_DATE] <= end_date]

    def immediate_rate(self, date):
        """
        Find and returns immediate rate effective on the date passed in

        :param date:    Date of the rate
        :return:        Immediate Rate effective on the date
        """
        rate = [d[Table.InterestRate.IMMEDIATE_RATE] for d in self.__data
                if d[Table.InterestRate.PRICE_DATE] <= date and d[Table.InterestRate.IMMEDIATE_RATE] is not None]
        return rate[-1] if len(rate) else self.three_month_rate(date)

    def three_month_rate(self, date):
        """
        Find and returns three-month rate effective on the date passed in

        :param date:    Date of the rate
        :return:        Three-Month Rate effective on the date
        """
        rate = [d[Table.InterestRate.THREE_MONTHS_RATE] for d in self.__data
                if d[Table.InterestRate.PRICE_DATE] <= date and d[Table.InterestRate.THREE_MONTHS_RATE] is not None]
        return rate[-1] if len(rate) else 0.0

    def __str__(self):
        return '%s, %s' % (self.__currency_code, self.__currency_id)
