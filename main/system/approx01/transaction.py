#!/usr/bin/python


class Transaction(object):

    def __init__(self, market, transaction_type, date, order_price, price, quantity, commission):
        self.__market = market
        self.__type = transaction_type
        self.__date = date
        self.__order_price = order_price
        self.__price = price
        self.__quantity = quantity
        self.__commission = commission

    def market(self):
        return self.__market

    def type(self):
        return self.__type

    def date(self):
        return self.__date

    def order_price(self):
        return self.__order_price

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def commission(self):
        return self.__commission

    def slippage(self):
        return abs(self.__price - self.__order_price)

    def __str__(self):
        return ' '.join([
            'Transaction',
            self.__type,
            self.__market.code(),
            str(self.__date),
            str(self.__price),
            str(int(self.__quantity)),
            str(self.__commission),
            str(float(self.slippage()))
        ])
