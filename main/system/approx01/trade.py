#!/usr/bin/python

from enum import Direction
from decimal import Decimal


class Trade(object):

    def __init__(self, position, order, order_result):
        self.__market = position.market()
        self.__direction = position.direction()
        self.__quantity = position.quantity()
        self.__enter_date = position.date()
        self.__enter_price = position.price()
        self.__enter_slip = abs(position.order_price() - position.price())
        self.__exit_date = order.date()
        self.__exit_price = order_result.price()
        self.__exit_slip = abs(order_result.price() - order.price())
        self.__commissions = order_result.commission() * 2  # TODO how about commissions during rolling?

    def market(self):
        return self.__market

    def direction(self):
        return self.__direction

    def enter_date(self):
        return self.__enter_date

    def enter_price(self):
        return self.__enter_price

    def enter_slip(self):
        return self.__enter_slip

    def exit_date(self):
        return self.__exit_date

    def exit_price(self):
        return self.__exit_price

    def exit_slip(self):
        return self.__exit_slip

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
            float(self.result() * Decimal(self.__quantity) * self.__market.point_value()),
            float(self.slippage() * self.__market.point_value()),
            self.__commissions,
            self.__market.currency()
        )
