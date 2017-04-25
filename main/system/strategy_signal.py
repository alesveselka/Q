#!/usr/bin/python


class Signal(object):

    def __init__(self, market, type, direction, date, price):
        self.__market = market
        self.__type = type
        self.__direction = direction
        self.__date = date
        self.__price = price

    def market(self):
        return self.__market

    def type(self):
        return self.__type

    def direction(self):
        return self.__direction

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def __str__(self):
        return ', '.join([
            self.__market.code(),
            self.__type,
            self.__direction,
            str(self.__date),
            str(self.__price)
        ])
