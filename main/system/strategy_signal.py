#!/usr/bin/python


class Signal(object):

    # def __init__(self, market, type, direction, date, price, forecast=None):
    def __init__(self, date, market, contract, forecast, price):
        self.__date = date
        self.__market = market
        self.__contract = contract
        # self.__type = type
        # self.__direction = direction
        self.__forecast = forecast
        self.__price = price

    def date(self):
        return self.__date

    def market(self):
        return self.__market

    def contract(self):
        return self.__contract

    # def type(self):
    #     return self.__type

    # def direction(self):
    #     return self.__direction

    def forecast(self):
        return self.__forecast

    def price(self):
        return self.__price

    def __str__(self):
        # return ', '.join([
        #     self.__market.code(),
        #     self.__type,
        #     self.__direction,
        #     str(self.__date),
        #     str(self.__price)
        # ])
        return ', '.join([
            str(self.__date),
            self.__market.code(),
            self.__contract,
            self.__forecast,
            str(self.__price)
        ])
