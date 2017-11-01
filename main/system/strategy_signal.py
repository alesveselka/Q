#!/usr/bin/python


class Signal(object):

    def __init__(self, date, market, contract, forecast, price):
        self.__date = date
        self.__market = market
        self.__contract = contract
        self.__forecast = forecast
        self.__price = price

    def date(self):
        return self.__date

    def market(self):
        return self.__market

    def contract(self):
        return self.__contract

    def forecast(self):
        return self.__forecast

    def price(self):
        return self.__price

    def __str__(self):
        return ', '.join([
            str(self.__date),
            self.__market.code(),
            self.__contract,
            self.__forecast,
            str(self.__price)
        ])
