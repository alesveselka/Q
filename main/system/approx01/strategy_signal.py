#!/usr/bin/python


class Signal(object):

    def __init__(self, code, direction, date, price):
        self.__code = code
        self.__direction = direction
        self.__date = date
        self.__price = price

    def code(self):
        return self.__code

    def direction(self):
        return self.__direction

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def __str__(self):
        return ', '.join([
            self.__code,
            self.__direction,
            str(self.__date),
            str(self.__price)
        ])[:-2]
