#!/usr/bin/python


class Order(object):

    def __init__(self, market, order_type, signal_type, date, price, quantity, contract):
        self.__market = market
        self.__type = order_type
        self.__contract = contract
        self.__date = date
        self.__price = price
        self.__quantity = quantity
        self.__signal_type = signal_type

    def market(self):
        return self.__market

    def contract(self):
        return self.__contract

    def type(self):
        return self.__type

    def signal_type(self):
        return self.__signal_type

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def __str__(self):
        return 'Order: %d x %s %s @ %.4f' % (
            self.__quantity,
            self.__type,
            self.__market.code(),
            self.__price
        )
