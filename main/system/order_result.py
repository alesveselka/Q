#!/usr/bin/python


class OrderResult(object):

    def __init__(self, result_type, order, price, quantity, margin, commission):
        self.__type = result_type
        self.__order = order
        self.__price = price
        self.__quantity = quantity
        self.__margin = margin
        self.__commission = commission

    def type(self):
        return self.__type

    def order(self):
        return self.__order

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def margin(self):
        return self.__margin

    def commission(self):
        return self.__commission

    def __str__(self):
        return 'Result: %d x @ %.4f' % (
            self.__quantity,
            self.__price
        )
