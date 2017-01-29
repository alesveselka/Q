#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from hft_data import HFTHistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from hft_portfolio import HFTPortfolio


class IntradayOLSMRStrategy(Strategy):
    """
    Uses ordinary least squares (OSL) to perform a rolling linear
    regression to determine the hedge ratio between a pair of equities.
    The z-score of the residuals time series is then calculated in
    a rolling fashion and if it exceeds an interval of thresholds
    (defaulting to [0.5, 3.0]) then a long/short signal pair are
    generated (for the high threshold) of an exit signal pair are
    generated (for the low threshold).
    """

    def __init__(self, bars, events, ols_window=100,
                 zscore_low=0.5, zscore_high=3.0):
        """
        Initializes the stat arb strategy.

        :param bars:        The DataHandler object that provides
                            bar information.
        :param events:      The Event Queue object
        :param ols_window:
        :param zscore_low:
        :param zscore_high:
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.ols_window = ols_window
        self.zscore_low = zscore_low
        self.zscore_high = zscore_high

        self.pair = ('AREX', 'WLL')
        self.datetime = dt.datetime.utcnow()

        self.long_market = False
        self.short_market = False

    def calculate_xy_signals(self, zscore_last):
        """
        Calculates the actual x, y signal pairings
        to be sent to the signal generator.

        Parameters:
        zscore_last     The current zscore to test against
        """
        x_signal = None
        y_signal = None
        p0 = self.pair[0]
        p1 = self.pair[1]
        now = self.datetime
        hedge_ratio = abs(self.hedge_ratio)

        # If we're long the market and below
        # the negative of the high zscore threshold
        if zscore_last <= -self.zscore_high and not self.long_market:
            self.long_market = True
            y_signal = SignalEvent(1, p0, now, 'LONG', 1.0)
            x_signal = SignalEvent(1, p1, now, 'SHORT', hedge_ratio)

        # If we're long the market and between
        # the absolute value of the low zscore threshold.
        if abs(zscore_last) <= self.zscore_low and self.long_market:
            self.long_market = False
            y_signal = SignalEvent(1, p0, now, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, now, 'EXIT', 1.0)

        # If we're short the market and above
        # the high zscore threshold
        if zscore_last >= self.zscore_high and not self.short_market:
            self.short_market = True
            y_signal = SignalEvent(1, p0, now, 'SHORT', 1.0)
            x_signal = SignalEvent(1, p1, now, 'LONG', hedge_ratio)

        # If we're short the market and between
        # the absolute value of the low zscore threshold.
        if abs(zscore_last) <= self.zscore_low and self.short_market:
            self.short_market = False
            y_signal = SignalEvent(1, p0, now, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, now, 'EXIT', 1.0)

        return y_signal, x_signal

    def calculate_signals_for_pairs(self):
        """
        Generates a new set of signals based on the mean reversion
        strategy.

        Calculates the hedge ratio between the pair of tickers.
        We use OLS for this, although we should ideally use CADF.
        """
        # Obtain the latest window of values
        # for each component of the pair of the tickers
        y = self.bars.get_latest_bar_values(self.pair[0], 'close', N=self.ols_window)
        x = self.bars.get_latest_bar_values(self.pair[1], 'close', N=self.ols_window)

        if y is not None and x is not None:
            # Check that all window periods are available
            if len(y) >= self.ols_window and len(x) >= self.ols_window:
                # Calculate the current hedge ratio using OSL
                self.hedge_ratio = sm.OLS(y, x).fit().params[0]

                # Calculate the current z-score of the residuals
                spread = y - self.hedge_ratio * x
                zscore_last = ((spread - spread.mean()) / spread.std())[-1]

                # Calculate signals and add to the event queue
                y_signal, x_signal = self.calculate_xy_signals(zscore_last)
                if y_signal is not None and x_signal is not None:
                    self.events.put(y_signal)
                    self.events.put(x_signal)

    def calculate_signals(self, event):
        """
        Calculate the SignalEvents based on the market data.
        """
        if event.type == 'MARKET':
            self.calculate_signals_for_pairs()

if __name__ == '__main__':
    csv_dir = 'resources/'
    symbol_list = ['AREX', 'WLL']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = dt.datetime(2007, 11, 8, 10, 41, 0)
    backtest = Backtest(
        csv_dir, symbol_list, initial_capital, heartbeat, start_date,
        HFTHistoricCSVDataHandler, SimulatedExecutionHandler,
        HFTPortfolio, IntradayOLSMRStrategy
    )
    backtest.simulate_trading()
