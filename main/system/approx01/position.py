#!/usr/bin/python


class Position(object):

    def __init__(self, signal, quantity):
        self.__code = signal.code()
        self.__direction = signal.direction()
        self.__date = signal.date()  # TODO enter day will be signal date + 1 (opened next day)
        self.__price = signal.price()
        self.__quantity = quantity

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
