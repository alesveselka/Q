#!/usr/bin/python


class Market(object):

    def __init__(self, connection, start_date, market_id, name, code, data_codes, currency, first_data_date, group):
        self.__connection = connection
        self.__start_date = start_date
        self.__id = market_id
        self.__name = name
        self.__code = code
        self.__data_codes = data_codes
        self.__currency = currency
        self.__first_data_date = first_data_date
        self.__group = group
        self.__data = []

    def __back_adjusted_data(self):
        cursor = self.__connection.cursor()
        code = ''.join([self.__code, '2']) if 'C' in self.__data_codes else self.__code
        sql = """
            SELECT code, price_date, open_price, high_price, low_price, settle_price
            FROM continuous_back_adjusted
            WHERE market_id = '%s'
            AND code = '%s'
            AND DATE(price_date) >= '%s';
        """

        cursor.execute(sql % (self.__id, code, self.__start_date.strftime('%Y-%m-%d')))
        self.__data = cursor.fetchall()

        # print code, len(data), data[0]

    def update_studies(self):
        self.__back_adjusted_data()

    def data(self, date):
        return [d for d in self.__data if d[1] == date]
