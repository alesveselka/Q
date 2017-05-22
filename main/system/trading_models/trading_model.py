#!/usr/bin/python

from abc import ABCMeta, abstractmethod


class TradingModel:
    """
    Abstract Base Class for all trading models
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        raise NotImplementedError("Should implement 'signals()'")
