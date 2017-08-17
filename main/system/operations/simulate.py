#!/usr/bin/python

import datetime as dt
from enum import EventType
from enum import Interval
from enum import SignalType
from enum import OrderResultType
from enum import Study
from enum import Table
from position import Position
from report import Report
from order import Order
from timer import Timer
from order_result import OrderResult
from persist import Persist
from itertools import combinations
from collections import defaultdict


class Simulate:

    def __init__(self, simulation, roll_strategy, data_series, risk, account, broker, portfolio, trading_model):
        self.__simulation = simulation
        self.__roll_strategy = roll_strategy
        self.__data_series = data_series
        self.__risk = risk
        self.__account = account
        self.__broker = broker
        self.__portfolio = portfolio
        self.__trading_model = trading_model
        self.__trading_signals = []
        self.__order_results = []
        self.__timer = Timer()

        now = dt.datetime.now()
        # end_date = dt.date(now.year, now.month, now.day)
        # end_date = dt.date(1992, 6, 10)
        end_date = dt.date(1992, 12, 31)

        self.__data_series.load(end_date, roll_strategy[Table.RollStrategy.ID])
        self.__subscribe()

        self.__start(data_series.start_date(), end_date)

    def __subscribe(self):
        """
        Subscribe to listen timer's events
        """
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        # self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)
        self.__timer.on(EventType.EOD_DATA, self.__on_eod_data)

    def __start(self, start_date, end_date):
        """
        Start the simulation
        
        :param start_date:  start date fo the simulation
        :param end_date:    end date of the simulation
        """
        self.__timer.on(EventType.COMPLETE, self.__on_timer_complete)
        self.__timer.start(start_date, end_date)

    def __on_timer_complete(self, date):
        """
        Timer Complete event handler

        :param date:    date of the complete event
        """
        start_date = self.__data_series.start_date()
        report = Report(self.__account)
        # print '\n'.join(report.transactions(start_date, date))
        # print '\n'.join(report.to_lists(start_date, date, Interval.YEARLY))
        # report.to_lists(start_date, date, Interval.MONTHLY)
        # print '\n'.join(report.to_lists(start_date, date))
        full_report = '\n'.join(report.to_lists(start_date, date))

        print full_report

        Persist(
            self.__simulation[Table.Simulation.ID],
            self.__roll_strategy,
            start_date,
            date,
            self.__order_results,
            self.__account,
            self.__portfolio,
            self.__data_series
        )

        # f = open('2_report_full_1993-12-31.txt', 'w')
        # f.write(full_report)
        # f.close()
        #
        # f = open('2_report_yearly_1993-12-31.txt', 'w')
        # f.write('\n'.join(report.to_lists(start_date, date, Interval.YEARLY)))
        # f.close()
        #
        # f = open('2_transactions_1993-12-31.txt', 'w')
        # f.write('\n'.join(report.transactions(start_date, date)))
        # f.close()

    def __on_market_open(self, date, previous_date):
        """
        Market Open event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # Update all data (Open, High, Low, Settle, ...) although only 'open' price is available now.
        # The reason is to enclose slipped price in high - low range when executed on open,
        # and also for simpler and faster calculations
        self.__data_series.update_futures_data(date)

        self.__transfer_orders(self.__orders(date))

        markets = [p.market() for p in self.__portfolio.open_positions()]
        if len(markets) >= 2:
            market_ids = {str(m.id()): m for m in markets}
            pairs = list(combinations(market_ids.keys(), 2))
            counter = defaultdict(int)
            fraction = .25
            print date, market_ids.keys(), pairs
            for pair in pairs:
                correlation = market_ids[pair[0]].correlation(date, pair[1])
                rounded_correlation = abs(fraction * round(correlation/fraction)) if correlation else None
                counter[rounded_correlation] += 1
                print pair, correlation, rounded_correlation
            print counter

    def __on_market_close(self, date, previous_date):
        """
        Market Close event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # self.__broker.update_account(date, previous_date, self.__portfolio.open_positions())

    def __on_eod_data(self, date, previous_date):
        """
        End-of-Day event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        self.__data_series.update_futures_studies(date)

        self.__broker.update_account(date, previous_date, self.__portfolio.open_positions())

        self.__trading_signals += self.__trading_model.signals(date, self.__portfolio.open_positions())

    def __transfer_orders(self, orders):
        """
        Transfer orders to broker

        :param orders:  list of order objects
        """
        for order in orders:
            order_result = order.quantity() \
                           and self.__broker.transfer(order, self.__portfolio.open_positions()) \
                           or OrderResult(OrderResultType.REJECTED, order, 0, 0, 0, 0)
            result_type = order_result.type()

            if result_type == OrderResultType.FILLED or result_type == OrderResultType.PARTIALLY_FILLED:
                signal_type = order.signal_type()
                if signal_type == SignalType.ENTER:
                    self.__portfolio.add_position(Position(order_result))

                if signal_type == SignalType.ROLL_ENTER or signal_type == SignalType.ROLL_EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)

                if signal_type == SignalType.EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)
                    self.__portfolio.remove_position(position)

            self.__order_results.append(order_result)

    def __orders(self, date):
        """
        Generate Orders from Signals

        :param date:    date for the market open
        """
        orders = []
        signals_to_remove = []

        for signal in self.__trading_signals:
            market = signal.market()
            market_data, previous_data = market.data(date)

            if market_data:
                atr_long = market.study(Study.ATR_LONG, previous_data[Table.Market.PRICE_DATE])[Table.Study.VALUE]
                open_price = market_data[Table.Market.OPEN_PRICE]
                enter_signals = [s for s in self.__trading_signals if s.type() == SignalType.ENTER]
                exit_signals = [s for s in self.__trading_signals if s.type() == SignalType.EXIT]
                roll_signals = [s for s in self.__trading_signals if s.type() == SignalType.ROLL_ENTER or s.type() == SignalType.ROLL_EXIT]
                market_position = self.__portfolio.market_position(market)

                if market_position and (signal in exit_signals or signal in roll_signals):
                    contract = market.contract(date) if signal.type() == SignalType.ROLL_ENTER else market_position.contract()
                    orders.append(Order(market, signal, date, open_price, market_position.quantity(), contract))

                if market_position is None and signal in enter_signals:
                    quantity = self.__risk.position_size(market.point_value(), market.currency(), atr_long, date)
                    orders.append(Order(market, signal, date, open_price, quantity, market.contract(date)))

                signals_to_remove.append(signal)

        for signal in signals_to_remove:
            self.__trading_signals.remove(signal)

        return orders
