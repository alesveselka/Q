#!/usr/bin/python

from math import floor
from decimal import Decimal
from enum import Table
from enum import Study
from enum import Direction


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

    def stop_loss(self, date, position):
        """
        Calculate and return Stop Loss price for the position and date passed in
        
        :param date:        date on when to calculate the stop loss
        :param position:    position for which to calculate the stop loss
        :return:            Decimal price representing the stop loss
        """
        market = position.market()
        position_data = market.data(position.enter_date(), date)
        prices = [d[Table.Market.SETTLE_PRICE] for d in position_data]
        atr = market.study(Study.ATR_SHORT, date)[-1][Table.Study.VALUE]  # TODO ATR_LONG?
        risk = 3 * atr
        return max(prices) - risk if position.direction() == Direction.LONG else min(prices) + risk
