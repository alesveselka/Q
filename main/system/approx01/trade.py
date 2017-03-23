#!/usr/bin/python

from enum import Direction
from decimal import Decimal


class Trade(object):

    def __init__(self, market, direction, quantity, enter_date, enter_price, enter_slip, exit_date, exit_price, exit_slip, commissions):
        self.__market = market
        self.__direction = direction
        self.__quantity = quantity
        self.__enter_date = enter_date
        self.__enter_price = enter_price
        self.__enter_slip = enter_slip
        self.__exit_date = exit_date
        self.__exit_price = exit_price
        self.__exit_slip = exit_slip
        self.__commissions = commissions

    def market(self):
        return self.__market

    def quantity(self):
        return self.__quantity

    def commissions(self):
        return self.__commissions

    def result(self):
        if self.__direction == Direction.LONG:
            return self.__exit_price - self.__enter_price
        if self.__direction == Direction.SHORT:
            return self.__enter_price - self.__exit_price

    def slippage(self):
        return (self.__enter_slip + self.__exit_slip) * Decimal(self.__quantity)

    def __str__(self):
        return '%s, %s, %d, Enter at %.2f(%.2f) on %s, Exit at %.2f(%.2f) on %s, (pts: %.2f, %.2f, s: %.2f, c: %.2f) %s' % (
            self.__market.code(),
            self.__direction,
            self.__quantity,
            self.__enter_price,
            self.__enter_slip,
            str(self.__enter_date),
            self.__exit_price,
            self.__exit_slip,
            str(self.__exit_date),
            self.result(),
            float(self.result() * Decimal(self.__quantity) * self.__market.point_value()),  # TODO convert non-base-currency to the base-currency value
            float(self.slippage() * self.__market.point_value()),
            self.__commissions,
            self.__market.currency()
        )
