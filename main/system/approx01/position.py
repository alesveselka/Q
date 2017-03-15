#!/usr/bin/python


class Position(object):

    def __init__(self, code, direction, date, price, quantity):
        self.__code = code
        self.__direction = direction
        self.__date = date
        self.__price = price
        self.__quantity = quantity

    def code(self):
        return self.__code

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
            self.__code,
            self.__direction,
            str(self.__date),
            str(self.__price),
            str(self.__quantity)
        ])
