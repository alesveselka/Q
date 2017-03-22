#!/usr/bin/python


class OrderResult(object):

    def __init__(self, result_type, date, price):
        self.__type = result_type
        self.__date = date
        self.__price = price

    def type(self):
        return self.__type

    def date(self):
        return self.__date

    def price(self):
        return self.__price
