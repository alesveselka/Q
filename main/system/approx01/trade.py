#!/usr/bin/python

from enum import Direction
from decimal import Decimal


class Trade(object):

    def __init__(self, market, direction, quantity, enter_date, enter_price, exit_date, exit_price):
        self.__market = market
        self.__direction = direction
        self.__quantity = quantity
        self.__enter_date = enter_date
        self.__enter_price = enter_price
        self.__exit_date = exit_date
        self.__exit_price = exit_price

    def market(self):
        return self.__market

    def quantity(self):
        return self.__quantity

    def result(self):
        if self.__direction == Direction.LONG:
            return self.__exit_price - self.__enter_price
        if self.__direction == Direction.SHORT:
            return self.__enter_price - self.__exit_price

    def __str__(self):
        return ', '.join([
            self.__market.code(),
            self.__direction,
            str(self.__quantity),
            'ENTER: ',
            str(self.__enter_date),
            str(self.__enter_price),
            'EXIT: ',
            str(self.__exit_date),
            str(self.__exit_price),
            ''.join(['(',
                str(float(self.result())),
                ', ',
                str(float(self.result() * Decimal(self.__quantity) * self.__market.point_value())),  # TODO convert non-base-currency to the base-currency value
                ')'
            ])
        ])
