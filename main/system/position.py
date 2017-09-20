#!/usr/bin/python

from enum import Direction
from enum import SignalType
from enum import OrderType
from enum import OrderResultType


class Position(object):

    def __init__(self, order_result):
        order = order_result.order()
        self.__market = order.market()
        self.__direction = {OrderType.BTO: Direction.LONG, OrderType.STO: Direction.SHORT}.get(order.type())
        self.__quantity = order_result.quantity()
        self.__enter_date = order_result.order().date()
        self.__enter_price = order_result.price()
        self.__margins = [(order_result.order().date(), order_result.margin())]
        self.__pnl = []
        self.__order_results = [order_result]

    def market(self):
        return self.__market

    def direction(self):
        return self.__direction

    def enter_date(self):
        return self.__enter_date

    def enter_price(self):
        return self.__enter_price

    def exit_date(self):
        last_order = self.__order_results[-1].order()
        return last_order.date() \
            if last_order.signal_type() == SignalType.EXIT \
            else None

    def exit_price(self):
        last_order_result = self.__order_results[-1]
        return last_order_result.price() \
            if last_order_result.order().signal_type() == SignalType.EXIT \
            else None

    def quantity(self):
        return self.__quantity

    def position_quantity(self, date):
        """
        Position quantity is quantity before the orders were executed on the date
        
        :param date:    date of the orders
        :return:        number representing position quantity
        """
        order_results = [r for r in self.__order_results if r.order().date() == date]
        position_quantity = self.__quantity

        for order_result in order_results:
            order_type = order_result.order().type()
            if order_result.order().signal_type() == SignalType.REBALANCE:
                position_quantity -= order_result.quantity() if order_type == OrderType.BTO or order_type == OrderType.STO else 0
            else:
                position_quantity -= order_result.quantity()

        return position_quantity if position_quantity > 0 else 0

    def commissions(self):
        return sum([r.commission() for r in self.__order_results])

    def order_results(self):
        return self.__order_results

    def add_order_result(self, order_result):
        self.__order_results.append(order_result)
        self.__update_quantity(order_result)

    def __update_quantity(self, order_result):
        order_type = order_result.order().type()
        quantity = order_result.quantity()
        self.__quantity += quantity if order_type == OrderType.BTO or order_type == OrderType.STO else -quantity

    def margins(self):
        return self.__margins

    def add_margin(self, date, margin):
        self.__margins.append((date, margin))

    def contract(self):
        """
        Find and return contract the position is currently open in
        
        :return:    string representing the futures contract
        """
        return self.__open_order_results()[-1].order().contract()

    def update_pnl(self, date, price, result, quantity):
        self.__pnl.append((date, price, result, quantity))

    def prices(self):
        """
        Return prices of position time span
        
        :return:    list of settle prices
        """
        return [p[1] for p in self.__pnl]

    def pnl(self):
        """
        Return sum of all P/Ls

        :return:    Sum of all Profit and Losses
        """
        return sum(p[2] for p in self.__pnl)

    def __open_order_results(self):
        """
        Return OrderResults of order type either BTO ot STO

        :return:    list of OrderResult instances
        """
        return [r for r in self.__order_results
                if r.order().type() == OrderType.BTO or r.order().type() == OrderType.STO]

    def __str__(self):
        """
        String representation of the position instance

        :return:    String
        """
        return '%s %d x %s at %4f on %s' % (
            self.__direction,
            self.__quantity,
            self.__market.code(),
            self.__enter_price,
            self.__enter_date
        )
