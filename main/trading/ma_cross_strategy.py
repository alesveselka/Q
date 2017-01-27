#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio


class MovingAverageCrossStrategy(Strategy):
    """
    Carries out a basic Moving Average Crossover strategy with
    a long/short simple weighted moving average. Default short / long 
    windows are 100/400 periods respectively.
    """

    def __init__(self, bars, events, short_window=100, long_window=400):
        """
        Initializes the Moving Average Crossover strategy.

        Parameters:
        bars            The DataHandler object that provides bar information.
        events          The Event Queue object.
        short_window    The short moving average lookback.
        long_window     The long moving average lookback.
        """
        self.bars = bars
        self.events = events
        self.short_window = short_window
        self.long_window = long_window
        self.symbol_list = self.bars.symbol_list

        # Set to True if a symbol is in the market
        self.bought = self.__calculate_initial_bought()
