#!/usr/bin/python


class OrderResult(object):

    def __init__(self, result_type, price):
        self.__type = result_type
        self.__price = price

    def type(self):
        return self.__type

    def price(self):
        return self.__price
