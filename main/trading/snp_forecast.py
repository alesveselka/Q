#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, 'main/model/')

from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio
from forecast import create_lagged_series


class SPYDailyForecastStrategy(Strategy):
    """
    S&P500 forecast strategy. It uses Quadratic Discriminant Analyser
    to predict the returns for a subsequent time period and then
    generated long/exit signals based on the prediction.
    """
    def __init__(self, bars, events):
        """
        Initializes the strategy.

        :param bars:    The DataHandler bars object.
        :param events:  The Event Queue object.
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.datetime_now = dt.datetime.utcnow()

        self.model_start_date = dt.datetime(2001, 1, 10)
        self.model_end_date = dt.datetime(2005, 12, 31)
        self.model_start_test_date = dt.datetime(2005, 1, 1)

        self.long_market = False
        self.short_market = False
        self.bar_index = 0

        self.model = self.create_symbol_forecast_model()

    def create_symbol_forecast_model(self):
        # Create a lagged series of the S&P500 US stock market index
        snp_returns = create_lagged_series(
            self.symbol_list[0], self.model_start_date,
            self.model_end_date, lags=5
        )
        # Use the prior two days of returns as predictor
        # values, with direction as response
        X = snp_returns[['Lag1', 'Lag2']]
        y = snp_returns['Direction']

        # Create training and test sets
        start_test = self.model_start_test_date
        X_train = X[X.index < start_test]
        X_test = X[X.index >= start_test]
        y_train = y[y.index < start_test]
        y_test = y[y.index >= start_test]

        model = QDA()
        model.fit(X_train, y_train)
        return model

    def calculate_signals(self, event):
        """
        Calculate SignalEvents based on market data.
        """
        symbol = self.symbol_list[0]
        now = self.datetime_now

        if event.type == 'MARKET':
            self.bar_index += 1
            if self.bar_index > 5:
                lags = self.bars.get_latest_bar_values(
                    symbol, 'adj_close', N=3
                )
                pred_series = pd.Series({
                    'Lag1': lags[1] * 100.0,
                    'Lag2': lags[2] * 100.0
                })
                pred = self.model.predict(pred_series)
                if pred > 0 and not self.long_market:
                    self.long_market = True
                    signal = SignalEvent(1, symbol, now, 'LONG', 1.0)
                    self.events.put(signal)
                if pred < 0 and self.long_market:
                    self.long_market = False
                    signal = SignalEvent(1, symbol, now, 'EXIT', 1.0)
                    self.events.put(signal)

if __name__ == '__main__':
    csv_dir = './resources/'
    symbol_list = ['AAPL']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = dt.datetime(2006, 1, 3)

    backtest = Backtest(
        csv_dir, symbol_list, initial_capital, heartbeat,
        start_date, HistoricCSVDataHandler, SimulatedExecutionHandler,
        Portfolio, SPYDailyForecastStrategy
    )
    backtest.simulate_trading()
