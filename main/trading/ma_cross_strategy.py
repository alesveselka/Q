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

    def __calculate_initial_bought(self):
        """
        Adds keys to the bought dictionary for all symbols
        and sets them to 'OUT'.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought

    def calculate_signals(self, event):
        """
        Generates a new set of signals based on the MAC SMA 
        with the short window crossing the long window meaning
        a long entry and vice versa for a short entry.

        Parameters:
        events  A MarketEvent object.
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bar_values(
                    s, 'adj_close', N=self.long_window
                )
                bar_date = self.bars.get_latest_bar_datetime(s)

                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    symbol = s
                    now = dt.datetime.utcnow()
                    sig_dir = ''

                    if short_sma > long_sma and self.bought == 'OUT':
                        print 'LONG: %s' % bar_date
                        sig_dir = 'LONG'
                        signal = SignalEvent(1, symbol, now, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == 'LONG':
                        print 'SHORT: %s' % bar_date
                        sig_dir = 'EXIT'
                        signal = SignalEvent(1, symbol, now, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'
