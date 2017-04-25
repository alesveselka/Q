#!/usr/bin/python


class OrderResult(object):

    def __init__(self, result_type, order, price, margin, commission):
        self.__type = result_type
        self.__order = order
        self.__price = price
        self.__margin = margin
        self.__commission = commission

    def type(self):
        return self.__type

    def order(self):
        return self.__order

    def price(self):
        return self.__price

    def margin(self):
        return self.__margin

    def commission(self):
        return self.__commission
