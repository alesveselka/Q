#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import datetime as dt
import os, os.path
import numpy as np
import pandas as pd
from event import MarketEvent

class DataHandler(object):
    """
    DataHandler is an abstract base class providing an interface for 
    all subsequent (inherited) data handlers (both live and historic).

    The goal of a (derived) DataHandler object is to output a generated
    set of bars (OHLCVI) for each symbol requested.

    This will replicate how a live strategy would function as current
    market data would be sent "down the pipe". Thus a historic and live
    system will be treated identically by the rest of the backtesting
    suite.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        Returns the latest bar updated.
        """
        raise NotImplementedError("Should implement 'get_latest_bar()'")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars updated.
        """
        raise NotImplementedError("Should implement 'get_latest_bars()'")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the latest bar.
        """
        raise NotImplementedError(
            "Should implement 'get_latest_bar_datetime()'"
        )

    @abstractmethod
    def get_latest_bar_value(self, symbol, type):
        """
        Returns one of the Open, High, Low, Close, Volume, or OI
        from the last bar.
        """
        raise NotImplementedError(
            "Should implement 'get_latest_bar_value()'"
        )

    @abstractmethod
    def get_latest_bar_values(self, symbol, type, N=1):
        """
        Returns the last N bar values from the latest_symbol list,
        or N-k if less available.
        """
        raise NotImplementedError(
            "Should implement 'get_latest_bar_values()'"
        )

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bars to the bars_queue for each symbol
        in a tuple OHLCVI format: (datetime, open, high, low, 
        close, volume, open interest).
        """
        raise NotImplementedError("Should implement 'update_bars()'")
