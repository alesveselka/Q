#!/usr/bin/python


class Trade(object):

    def __init__(self, code, direction, quantity, enter_date, enter_price, exit_date, exit_price):
        self.__code = code  # TODO replace with 'market'?
        self.__direction = direction
        self.__quantity = quantity
        self.__enter_date = enter_date
        self.__enter_price = enter_price
        self.__exit_date = exit_date
        self.__exit_price = exit_price

    def __str__(self):
        return ', '.join([
            self.__code,
            self.__direction,
            str(self.__quantity),
            'ENTER: ',
            str(self.__enter_date),
            str(self.__enter_price),
            'EXIT: ',
            str(self.__exit_date),
            str(self.__exit_price)
        ])
