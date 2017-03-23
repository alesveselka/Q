#!/usr/bin/python

from enum import Direction


class Position(object):

    def __init__(self, market, direction, date, order_price, price, quantity):
        self.__market = market
        self.__direction = direction
        self.__date = date
        self.__order_price = order_price
        self.__price = price
        self.__quantity = quantity
        self.__pnls = []

    def market(self):
        return self.__market

    def direction(self):
        return self.__direction

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def order_price(self):
        return self.__order_price

    def quantity(self):
        return self.__quantity

    def mark_to_market(self, date, price):
        """
        Calculates and saves P/L for the date and price passed in

        :param date:    Date of the P/L to be calculated
        :param price:   Number representing price to be marked
        :return:        Number representing calculated Profit or Loss in market points
        """
        previous_price = self.__pnls[-1][1] if len(self.__pnls) else self.__price
        pnl = (price - previous_price) if self.__direction == Direction.LONG else (previous_price - price)
        pnl_index = self.__pnl_index(date)  # TODO get previous price based on this index!

        if pnl_index > -1:
            self.__pnls[pnl_index] = (date, price, pnl)
        else:
            self.__pnls.append((date, price, pnl))

        return pnl

    def pnl(self):
        """
        Return sum of all P/Ls

        :return:    Sum of all Profit and Losses
        """
        return reduce(lambda result, item: result + item[2], self.__pnls, 0)

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

    def __str__(self):
        """
        String representation of the position instance

        :return:    String
        """
        return ', '.join([
            self.__market.code(),
            self.__direction,
            str(self.__date),
            str(self.__price),
            str(self.__quantity)
        ])
