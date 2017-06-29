#!/usr/bin/python

from enum import Direction
from enum import OrderType
from enum import SignalType


class Position(object):

    def __init__(self, order_result):
        order = order_result.order()
        self.__market = order.market()
        self.__direction = {OrderType.BTO: Direction.LONG, OrderType.STO: Direction.SHORT}.get(order.type())
        self.__quantity = order_result.quantity()
        self.__enter_date = order_result.order().date()
        self.__enter_price = order_result.price()
        self.__margins = [(order_result.order().date(), order_result.margin())]
        self.__pnls = []
        self.__order_results = [order_result]

    def market(self):
        return self.__market

    def direction(self):
        return self.__direction

    def enter_date(self):
        return self.__enter_date

    def latest_enter_date(self):
        return self.__open_order_results()[-1].order().date()

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

    def commissions(self):
        return sum([r.commission() for r in self.__order_results])

    def order_results(self):
        return self.__order_results

    def add_order_result(self, order_result):
        self.__order_results.append(order_result)

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

    def prices(self):
        """
        Return prices of position time span
        
        :return:    list of settle prices
        """
        return [p[1] for p in self.__pnls]

    def mark_to_market(self, date, price):
        """
        Calculates and saves P/L for the date and price passed in

        :param date:    Date of the P/L to be calculated
        :param price:   Number representing price to be marked
        :return:        Number representing calculated Profit or Loss in market points
        """
        if date == self.latest_enter_date():
            previous_price = self.__open_order_results()[-1].price()
        else:
            pnl_index = self.__pnl_index(date)
            previous_index = pnl_index - 1 if pnl_index > 0 else -1
            previous_price = self.__pnls[previous_index][1] if len(self.__pnls) else self.__enter_price

        pnl = (price - previous_price) if self.__direction == Direction.LONG else (previous_price - price)
        self.__pnls.append((date, price, pnl))

        return pnl

    def pnl(self):
        """
        Return sum of all P/Ls

        :return:    Sum of all Profit and Losses
        """
        return sum(p[2] for p in self.__pnls)

    def __pnl_index(self, date):
        """
        Find and return index of item which date is equal to the date passed in
        Returns -1 otherwise

        :param date:    Date
        :return:        Number
        """
        for i, pnl in enumerate(self.__pnls):
            if pnl[0] == date:
                return i
        return -1

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
