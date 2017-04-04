#!/usr/bin/python


class InterestRate(object):

    def __init__(self, currency_id, currency_code):
        self.__currency_id = currency_id
        self.__currency_code = currency_code
        self.__data = None

    def load_data(self, connection):
        cursor = connection.cursor()
        sql = """
            SELECT price_date, immediate_rate, three_months_rate
            FROM interest_rate
            WHERE currency_id = '%s';
        """

        cursor.execute(sql % self.__currency_id)
        self.__data = cursor.fetchall()

        print self.__currency_code, len(self.__data), self.__data[-1]

    def __str__(self):
        return '%s, %s' % (self.__currency_code, self.__currency_id)
