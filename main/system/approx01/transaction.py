#!/usr/bin/python


class Transaction(object):

    def __init__(self, market, transaction_type, date, price, quantity, commission):
        self.__market = market
        self.__type = transaction_type
        self.__date = date
        self.__price = price
        self.__quantity = quantity
        self.__commission = commission

    def market(self):
        return self.__market

    def type(self):
        return self.__type

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def commission(self):
        return self.__commission

    def __str__(self):
        return ' '.join([
            'Transaction',
            self.__market.code(),
            self.__type,
            str(self.__date),
            str(self.__price),
            str(self.__quantity),
            str(self.__commission)
        ])
