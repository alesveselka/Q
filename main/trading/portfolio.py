#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
from event import OrderEvent
from performance import create_sharpe_ratio
from performance import create_drawdowns


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
        self.symbol_list = self.bars.symbol_list
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
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        """
        Construct dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        d = self.__empty_positions(holdings=True)
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
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
        dh['commission'] = self.current_holdings['commission']
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

    def update_holdings_from_fill(self, fill):
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
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        """
        Simply files an Order object as a constant quantity
        sizing of the signal object, without risk management
        or position sizing considerations.

        Parameters:
        signal  The tuple containing signal information.
        """
        order = None
        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength
        market_quantity = 100
        current_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        if direction == 'LONG' and current_quantity == 0:
            order = OrderEvent(symbol, order_type, market_quantity, 'BUY')
        if direction == 'SHORT' and current_quantity == 0:
            order = OrderEvent(symbol, order_type, market_quantity, 'SELL')

        if direction == 'EXIT' and current_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(current_quantity), 'SELL')
        if direction == 'EXIT' and current_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(current_quantity), 'BUY')

        return order

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders
        based on the portfolio logic.
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def create_equity_curve_dataframe(self):
        """
        Creates a pandas DataFrame from the 'all_holdings'
        list of dictionaries.
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()

        self.equity_curve = curve

    def output_summary_stats(self):
        """
        Creates a list of summary statistics for the portfolio.
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns, periods=252)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown

        stats = [
            ('Total Return', '%0.2f%%' % ((total_return - 1.0) * 100.0)),
            ('Sharpe Ratio', '%0.2f' % sharpe_ratio),
            ('Max Drawdown', '%0.2f%%' % (max_dd * 100.0)),
            ('Drawdown Duration', '%d' % dd_duration),
        ]

        self.equity_curve.to_csv('equity.csv')

        return stats
