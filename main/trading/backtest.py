#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import pprint
import Queue as queue
import time


class Backtest(object):
    """
    Encapsulates the settings and components for carrying out
    an event-driven backtest.
    """

    def __init__(
            self, csv_dir, symbol_list, initial_capital,
            heartbeat, start_date, data_handler,
            execution_handler, portfolio, strategy
        ):
        """
        Initializes the backtest.

        Parameters:
        csv_dir             The hard root to the CSV data directory.
        symbol_list         The list of symbol strings.
        initial_capital     The starting capital for the portfolio.
        heartbeat           Backtest 'heartbeat' in seconds.
        start_date          The start datetime of the strategy.
        data_handler        (Class) Handles the market data feed.
        execution_handler   (Class) Handles the orders/fill for trades.
        portfolio           (Class) Keeps track of portfolio current 
                            and prior positions.
        strategy            (Class) Generates signals based on market data. 
        """
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.data_handler = data_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.strategy = strategy

        self.events = queue.Queue()

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1

        self.__generate_trading_instances()
