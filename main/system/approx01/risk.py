#!/usr/bin/python

from math import floor
from decimal import Decimal


class Risk(object):

    def __init__(self, position_sizing, account):
        self.__position_sizing = position_sizing
        self.__account = account

    def position_size(self, point_value, currency, atr, date):
        """
        Calculate and return position size based on market's point value, currency and ATR

        :param point_value:     Market contract point value
        :param currency:        Currency in which is market contract denominated
        :param atr:             Recent ATR
        :param date:            date on which return the position size
        :return:                Integer representing position quantity
        """
        return floor((self.__position_sizing * self.__account.equity(date)) /
                     Decimal(atr * self.__account.base_value(point_value, currency, date)))
