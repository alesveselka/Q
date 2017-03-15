#!/usr/bin/python


class Trade(object):

    def __init__(self, market, direction, quantity, enter_date, enter_price, exit_date, exit_price):
        self.__market = market
        self.__direction = direction
        self.__quantity = quantity
        self.__enter_date = enter_date
        self.__enter_price = enter_price
        self.__exit_date = exit_date
        self.__exit_price = exit_price

    def __str__(self):
        return ', '.join([
            self.__market.code(),
            self.__direction,
            str(self.__quantity),
            'ENTER: ',
            str(self.__enter_date),
            str(self.__enter_price),
            'EXIT: ',
            str(self.__exit_date),
            str(self.__exit_price)
        ])
