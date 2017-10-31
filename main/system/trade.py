#!/usr/bin/python


class Trade:

    def __init__(self, order, order_result):
        self.__order = order
        self.__order_result = order_result

    def order(self):
        return self.__order

    def order_result(self):
        return self.__order_result

    def __str__(self):
        return '%s, %s' % (self.__order, self.__order_result)
