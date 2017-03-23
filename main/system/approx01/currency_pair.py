#!/usr/bin/python


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

        print 'Data loaded: ', self.__code, len(self.__data), self.__data[-1][4]
