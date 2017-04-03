#!/usr/bin/python


class Order(object):

    def __init__(self, market, order_type, date, price, quantity, market_atr, market_volume):
        self.__market = market
        self.__type = order_type
        self.__date = date
        self.__price = price
        self.__quantity = quantity
        self.__market_atr = market_atr
        self.__market_volume = market_volume

    def market(self):
        return self.__market

    def type(self):
        return self.__type

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def market_atr(self):
        return self.__market_atr

    def market_volume(self):
        return self.__market_volume
