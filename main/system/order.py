#!/usr/bin/python


class Order(object):

    def __init__(self, date, market, contract, price, quantity):
        self.__date = date
        self.__market = market
        self.__contract = contract
        self.__price = price
        self.__quantity = quantity

    def market(self):
        return self.__market

    def contract(self):
        return self.__contract

    def date(self):
        return self.__date

    def price(self):
        return self.__price

    def quantity(self):
        return self.__quantity

    def __str__(self):
        return 'Order: %s %d x %s %s @ %.4f' % (
            'Buy' if self.__quantity > 0 else 'Sell',
            self.__quantity,
            self.__market.code(),
            self.__contract,
            self.__price
        )
