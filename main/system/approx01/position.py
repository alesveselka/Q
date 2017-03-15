#!/usr/bin/python


class Position(object):

    def __init__(self, market, direction, date, price, quantity):
        self.__market = market
        self.__direction = direction
        self.__date = date
        self.__price = price
        self.__quantity = quantity

    def market(self):
        return self.__market

    def direction(self):
        return self.__direction

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def __str__(self):
        return ', '.join([
            self.__market.code(),
            self.__direction,
            str(self.__date),
            str(self.__price),
            str(self.__quantity)
        ])
