#!/usr/bin/python


class OrderResult(object):

    def __init__(self, result_type, date, price, commission):
        self.__type = result_type
        self.__date = date
        self.__price = price
        self.__commission = commission

    def type(self):
        return self.__type

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def commission(self):
        return self.__commission
