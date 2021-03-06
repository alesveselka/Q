#!/usr/bin/python
# -*- coding: utf-8 -*-

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
            execution_handler, portfolio, strategy, parameter_list
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
        parameter_list      List of parameter dictionaries
        """
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date

        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy
        self.parameter_list = parameter_list

        self.events = queue.Queue()

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1

        self.__generate_trading_instances()

    def __generate_trading_instances(self, strategy_param_dict):
        """
        Generates the trading instance objects
        from their class types.
        """
        print "Creating DataHandler, Strategy, Portfolio and ExecutionHandler"
        print "Strategy parameter dict: %s" % strategy_param_dict
        self.data_handler = self.data_handler_cls(
            self.events,
            self.csv_dir,
            self.symbol_list
        )
        self.strategy = self.strategy_cls(
            self.data_handler,
            self.events,
            **strategy_param_dict
        )
        self.portfolio = self.portfolio_cls(
            self.data_handler,
            self.events,
            self.start_date,
            self.initial_capital
        )
        self.execution_handler = self.execution_handler_cls(
            self.events
        )

    def __run(self):
        """
        Executes the backtest.
        """
        i = 0
        while True:
            i += 1
            print i
            # Update the market bars
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
            else:
                break

            # Handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event)

            time.sleep(self.heartbeat)

    def __output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        self.portfolio.create_equity_curve_dataframe()

        print "Creating summary stats ..."
        stats = self.portfolio.output_summary_stats()

        print "Creating equity curve"
        print self.portfolio.equity_curve.tail(10)
        pprint.pprint(stats)

        print 'Signals: %s' % self.signals
        print 'Orders: %s' % self.orders
        print 'Fills: %s' % self.fills

    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        # out = open('output/opt.csv', 'w')

        spl = len(self.parameter_list)
        for i, sp in enumerate(self.parameter_list):
            print "Strategy %s out of %s ..." % (i+1, spl)
            self.__generate_trading_instances(sp)
            self.__run()
            self.__output_performance()
