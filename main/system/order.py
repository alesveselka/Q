#!/usr/bin/python

from enum import SignalType
from enum import Direction
from enum import OrderType


class Order(object):

    def __init__(self, market, signal, date, price, quantity, data):
        self.__market = market
        self.__contract = signal.contract()
        self.__date = date
        self.__price = price
        self.__quantity = quantity
        self.__market_data = data
        self.__signal_type = signal.type()
        self.__type = {
            SignalType.ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.EXIT: {Direction.LONG: OrderType.STC, Direction.SHORT: OrderType.BTC},
            SignalType.ROLL_ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.ROLL_EXIT: {Direction.LONG: OrderType.STC, Direction.SHORT: OrderType.BTC}
        }.get(self.__signal_type).get(signal.direction())

    def market(self):
        return self.__market

    def contract(self):
        return self.__contract

    def type(self):
        return self.__type

    def signal_type(self):
        return self.__signal_type

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def market_data(self):
        return self.__market_data

    def clear_market_data(self):
        self.__market_data = None

    def __str__(self):
        return 'Order: %d x %s %s @ %.4f' % (
            self.__quantity,
            self.__type,
            self.__market.code(),
            self.__price
        )
