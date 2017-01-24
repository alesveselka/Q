#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
from math import floor
from event import FillEvent, OrderEvent
from performance import create_sharpe_ratio
from performance import create_drawdowns
try:
    import Queue as queue
except ImportError:
    import queue

class Portfolio(object):
    """
    The Portfolio class handles the positions and market
    value of all instruments at a resolution of a 'bar',
    i.e. secondly, minutely, 5-min, 30-min, 60-min or EOD.

    The positions DataFrame stores a time-index of the
    quantity of positions held.

    The holdings DataFrame stores the cash and total market
    holdings value of each symbol for a particular time-index,
    as well as the percentage change in portfolio total 
    across bars.
    """

    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Initialises the portfolio object with bars and an event queue.
        Also includes a starting datetime index and initial capital
        (USD unless otherwise stated).

        Parameters:
        bars            The DataHandler object with current market data.
        event           The Event Queue object.
        start_date      The start date (bar) of the portfolio.
        initial_capital The starting capital in USD.
        """
        self.bars = bars
        self.events = events
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = self.__empty_positions()
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def __empty_positions(self, holdings=False):
        """
        "Create and returns empty position list.
        """
        if holdings:
            return dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        else:
            return dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])

    def construct_all_positions(self):
        """
        Construct the positions list using the start_date
        to determine when the time index will begin.
        """
        d = self.__empty_positions()
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self):
        """
        Construct the holdings list using the start_date
        to determine when the time index will begin.
        """
        d = self.__empty_positions(holdings=True)
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commision'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        """
        Construct dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        d = self.__empty_positions(holdings=True)
        d['cash'] = self.initial_capital
        d['commision'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current
        market data bar. This reflects the PREVIOUS bar, i.e. all 
        current market data at this stage is known (OHLCV).

        Makes use of a MarketEvent from the events queue.
        """
        latest_datetime = self.bars.get_latest_bar_datetime(
            self.symbol_list[0]
        )

        # Update positions
        # ================
        dp = self.__empty_positions()
        dp['datetime'] = latest_datetime

        for s in self.symbol_list:
            dp[s] = self.current_positions[s]

        # Append the current positions
        self.all_positions.append(dp)

        # Update holdings
        # ===============
        dh = self.__empty_positions()
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commision'] = self.current_holdings['commision']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[s] * \
                           self.bars.get_latest_bar_value(s, 'adj_close')
            dh[s] = market_value
            dh['total'] += market_value

        # Append the current holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the position matrix
        to reflect the new position.

        Parameters:
        fill    The Fill object to update the position with.
        """
        # Check whether the fill is buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def upate_holdings_from_fill(self, fill):
        """
        Takes a Fill object and updates the holdings matrix
        to reflect the holdings value.

        Parameters:
        fill    The Fill object to update the holdings with.
        """
        # Check whether the fill is buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, 'adj_close')
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commision'] += fill.commision
        self.current_holdings['cash'] -= (cost + fill.commision)
        self.current_holdings['total'] -= (cost + fill.commision)

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.upate_holdings_from_fill(event)
