#!/usr/bin/python


class Market(object):

    def __init__(self, connection, market_id, name, code, currency, first_data_date, group):
        self.__connection = connection
        self.__id = market_id
        self.__name = name
        self.__code = code
        self.__currency = currency
        self.__first_data_date = first_data_date
        self.__group = group

        self.__back_adjusted_data()

    def __back_adjusted_data(self):
        cursor = self.__connection.cursor()
        sql = """
            SELECT code, price_date, open_price, high_price, low_price, settle_price
            FROM continuous_back_adjusted
            WHERE market_id = '%s';
        """

        cursor.execute(sql % self.__id)
        data = cursor.fetchall()
