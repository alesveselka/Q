#!/usr/bin/python

import datetime as dt
from decimal import Decimal


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
            SELECT price_date, immediate_rate, three_months_rate
            FROM interest_rate
            WHERE currency_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date ASC;
        """

        cursor.execute(sql % (
            self.__currency_id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        self.__data = cursor.fetchall()

    def data(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Return list of data in the range specified by starting and ending dates passed in

        :param start_date:  Date, start fo the data range
        :param end_date:    Date, end of the data range
        :return:            List of data
        """
        return [d for d in self.__data if start_date <= d[0] <= end_date]

    def immediate_rate(self, date):
        """
        Find and returns immediate rate effective on the date passed in

        :param date:    Date of the rate
        :return:        Immediate Rate effective on the date
        """
        rate = [d[1] for d in self.__data if d[0] <= date and d[1] is not None]
        return rate[-1] if len(rate) else self.three_month_rate(date)

    def three_month_rate(self, date):
        """
        Find and returns three-month rate effective on the date passed in

        :param date:    Date of the rate
        :return:        Three-Month Rate effective on the date
        """
        rate = [d[2] for d in self.__data if d[0] <= date and d[2] is not None]
        return rate[-1] if len(rate) else Decimal(1)

    def __str__(self):
        return '%s, %s' % (self.__currency_code, self.__currency_id)
