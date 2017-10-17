#!/usr/bin/python

import datetime as dt
from enum import EventType
from enum import Interval
from enum import Direction
from enum import SignalType
from enum import OrderType
from enum import OrderResultType
from enum import Table
from position import Position
from report import Report
from order import Order
from timer import Timer
from strategy_signal import Signal
from order_result import OrderResult
from persist import Persist


class Simulate:

    def __init__(self,
                 simulation,
                 roll_strategy,
                 data_series,
                 risk,
                 account,
                 broker,
                 portfolio,
                 trading_model,
                 position_inertia,
                 use_position_inertia):
        self.__simulation = simulation
        self.__roll_strategy = roll_strategy
        self.__data_series = data_series
        self.__risk = risk
        self.__account = account
        self.__broker = broker
        self.__portfolio = portfolio
        self.__trading_model = trading_model
        self.__position_inertia = position_inertia
        self.__use_position_inertia = use_position_inertia
        self.__trading_signals = []
        self.__position_sizes = {}
        self.__order_results = []
        self.__timer = Timer()

        end_date = dt.date(1992, 5, 31)

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

        # f = open('report_full_1995-12-31_3.txt', 'w')
        # f.write(full_report)
        # f.close()
        #
        # f = open('report_daily_1995-12-31_3.txt', 'w')
        # f.write('\n'.join(report.to_lists(start_date, date, Interval.DAILY)))
        # f.close()
        #
        # f = open('transactions_1995-12-31_3.txt', 'w')
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

        # Account update
        open_positions = self.__portfolio.open_positions()
        removed_positions = self.__portfolio.removed_positions(date)
        self.__broker.update_account(date, previous_date, open_positions, removed_positions)

        # Trading signals and position sizing
        self.__trading_signals += self.__trading_model.signals(date, open_positions)
        forecasts = {s.market().id(): s.forecast() for s in self.__trading_signals if s.forecast()}

        open_markets, markets_to_open, markets_to_close, markets_to_roll = self.__partitioned_markets()
        markets_to_update = set(open_markets).difference(markets_to_close).union(markets_to_open)

        self.__position_sizes = self.__risk.position_sizes(date, markets_to_update, forecasts)

        if self.__use_position_inertia:
            self.__trading_signals += self.__rebalance_signals(date, open_markets, markets_to_close, markets_to_roll)

        self.__filter_illiquid_markets(markets_to_update)

    def __rebalance_signals(self, date, open_markets, markets_to_close, markets_to_roll):
        """
        Generate 'rebalance' trading signals
        
        :param date:                date of the data
        :param open_markets:        markets of actually opened positions
        :param markets_to_close:    markets of positions to be closed
        :param markets_to_roll:     markets of positions to be rolled to next contract
        :return:                    list of rebalance signals
        """
        rebalance_signals = []
        candidate_markets = set(open_markets).difference(markets_to_close).difference(markets_to_roll)

        for market in candidate_markets:
            market_data, _ = market.data(date)
            if market_data:
                market_position = self.__portfolio.market_position(market)
                if market_position:
                    quantity = float(market_position.quantity())
                    # TODO I don't need all quantity to rebalance -- rebalance only requires smaller part of position
                    # If the market ID is not in position sizes Dict, there is not enough liquidity
                    position_size = self.__position_sizes[market.id()] \
                        if market.id() in self.__position_sizes else market_position.quantity()
                    diff = (abs(abs(position_size) - quantity) / quantity) if quantity else 0.0

                    if diff > self.__position_inertia:
                        direction = market_position.direction()
                        price = market_data[Table.Market.OPEN_PRICE]
                        rebalance_signals.append(Signal(market, SignalType.REBALANCE, direction, date, price))

        return rebalance_signals

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

                if signal_type == SignalType.REBALANCE:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)

                if signal_type == SignalType.ROLL_ENTER or signal_type == SignalType.ROLL_EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)

                if signal_type == SignalType.EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)
                    self.__portfolio.remove_position(order.date(), position)

            self.__order_results.append(order_result)

    def __orders(self, date):
        """
        Generate Orders from Signals

        :param date:    date for the market open
        """
        orders = []
        signals_to_remove = []
        enter_signals = [s for s in self.__trading_signals if s.type() == SignalType.ENTER]
        exit_signals = [s for s in self.__trading_signals if s.type() == SignalType.EXIT]
        roll_signals = [s for s in self.__trading_signals if s.type() == SignalType.ROLL_ENTER or s.type() == SignalType.ROLL_EXIT]

        for signal in self.__trading_signals:
            market = signal.market()
            market_data, previous_data = market.data(date)

            if market_data:
                price = market_data[Table.Market.OPEN_PRICE]
                position = self.__portfolio.market_position(market)
                signal_type = signal.type()
                order_type = self.__order_type(signal.type(), signal.direction())

                if position and signal in exit_signals:
                    orders.append(Order(market, order_type, signal_type, date, price, position.quantity(), position.contract()))

                if position and signal in roll_signals:
                    quantity = abs(self.__position_sizes[market.id()]) if signal.type() == SignalType.ROLL_ENTER else position.quantity()
                    contract = market.contract(date) if signal.type() == SignalType.ROLL_ENTER else position.contract()
                    orders.append(Order(market, order_type, signal_type, date, price, quantity, contract))

                if position and signal_type == SignalType.REBALANCE:
                    quantity = abs(self.__position_sizes[market.id()]) - position.quantity()
                    order_type = self.__order_type(signal.type(), signal.direction(), quantity)
                    position_size = self.__position_sizes[market.id()]
                    position_direction = position.direction()
                    signal_direction = Direction.LONG if position_size >= 0 else Direction.SHORT
                    if signal_direction == position_direction:
                        orders.append(Order(market, order_type, signal_type, date, price, abs(quantity), position.contract()))
                    else:
                        order_type = self.__order_type(SignalType.EXIT, position_direction, position.quantity())
                        orders.append(Order(market, order_type, SignalType.EXIT, date, price, position.quantity(), position.contract()))
                        order_type = self.__order_type(SignalType.ENTER, signal_direction, abs(position_size))
                        orders.append(Order(market, order_type, SignalType.ENTER, date, price, abs(position_size), position.contract()))

                if position is None and signal in enter_signals:
                    position_size = abs(self.__position_sizes[market.id()])
                    orders.append(Order(market, order_type, signal_type, date, price, position_size, market.contract(date)))

                signals_to_remove.append(signal)

        for signal in signals_to_remove:
            self.__trading_signals.remove(signal)

        return orders

    def __order_type(self, signal_type, direction, position_difference=0.0):
        """
        Determine order type based on signal type, direction and optionally position difference
        
        :param signal_type:         type of signal
        :param direction:           direction of position
        :param position_difference: difference between current position size and new one, in case of rebalance signal
        :return: 
        """
        return {
            SignalType.ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.EXIT: {Direction.LONG: OrderType.STC, Direction.SHORT: OrderType.BTC},
            SignalType.ROLL_ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.ROLL_EXIT: {Direction.LONG: OrderType.STC, Direction.SHORT: OrderType.BTC},
            SignalType.REBALANCE: {
                Direction.LONG: OrderType.BTO if position_difference >= 0 else OrderType.STC,
                Direction.SHORT: OrderType.STO if position_difference >= 0 else OrderType.BTC
            }
        }.get(signal_type).get(direction)

    def __partitioned_markets(self):
        """
        Partition markets into list based on their signal types
        
        :return:    tuple ot list of markets
        """
        open_markets = sorted([p.market() for p in self.__portfolio.open_positions()])
        markets_to_open = sorted([s.market() for s in self.__trading_signals if s.type() == SignalType.ENTER])
        markets_to_close = sorted([s.market() for s in self.__trading_signals if s.type() == SignalType.EXIT])
        markets_to_roll = [s.market() for s in self.__trading_signals if s.type() == SignalType.ROLL_ENTER or s.type() == SignalType.ROLL_EXIT]
        return open_markets, markets_to_open, markets_to_close, markets_to_roll

    def __filter_illiquid_markets(self, position_sized_markets):
        """
        Filter illiquid market signals from trading signals
         
        :param set position_sized_markets:  markets with updated position size
        """
        illiquid_market_signals = [s for s in self.__trading_signals
                                   if s.market() in position_sized_markets
                                   and s.market().id() not in self.__position_sizes]
        # TODO mark the removed as Rejected
        for signal in illiquid_market_signals:
            self.__trading_signals.remove(signal)
