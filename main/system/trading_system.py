#!/usr/bin/python

from enum import Study
from enum import EventType
from enum import Direction
from enum import SignalType
from enum import OrderResultType
from enum import Table
from strategy_signal import Signal
from order import Order
from position import Position


class TradingSystem:

    def __init__(self, timer, markets, risk, portfolio, broker):
        self.__timer = timer
        self.__markets = markets
        self.__risk = risk
        self.__portfolio = portfolio
        self.__broker = broker
        self.__signals = []

    def subscribe(self):
        """
        Subscribe to listen timer's events
        """
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        self.__timer.on(EventType.EOD_DATA, self.__on_eod_data)

    def __on_market_open(self, date, previous_date):
        """
        Market Open event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        self.__transfer_orders(self.__generate_orders(date))

        # TODO what if signals will be deleted on holiday and next day no orders created?
        del self.__signals[:]

    def __on_eod_data(self, date, previous_date):
        """
        End-of-Day event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        self.__generate_signals(date, previous_date)

    def __generate_signals(self, date, previous_date):
        """
        Generate trading signals

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # TODO pass in the configuration of parameters
        short_window = 50
        long_window = 100

        for market in self.__markets:
            market_data = market.data(end_date=date)

            # TODO replace hard-coded data
            if len(market_data) >= long_window + 1 and market.has_data(date):
                previous_date = market_data[-2][Table.Market.PRICE_DATE]
                sma_long = market.study(Study.SMA_LONG, date)[-1][Table.Study.VALUE]
                sma_short = market.study(Study.SMA_SHORT, date)[-1][Table.Study.VALUE]
                hhll_short = market.study(Study.HHLL_SHORT, previous_date)[-1]
                settle_price = market_data[-1][Table.Market.SETTLE_PRICE]
                market_position = self.__portfolio.market_position(market)

                # TODO pass in rules
                if market_position:
                    direction = market_position.direction()
                    if direction == Direction.LONG:
                        if settle_price <= self.__risk.stop_loss(date, market_position):
                            self.__signals.append(Signal(market, SignalType.EXIT, Direction.SHORT, date, settle_price))
                    elif direction == Direction.SHORT:
                        if settle_price >= self.__risk.stop_loss(date, market_position):
                            self.__signals.append(Signal(market, SignalType.EXIT, Direction.LONG, date, settle_price))

                    # Naive contract roll implementation (end of each month)
                    if date.month != previous_date.month and len(self.__signals) == 0:
                        opposite_direction = Direction.LONG if direction == Direction.SHORT else Direction.LONG
                        self.__signals.append(Signal(market, SignalType.ROLL_EXIT, opposite_direction, date, settle_price))
                        self.__signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, settle_price))

                # TODO pass-in rules
                if sma_short > sma_long:
                    if settle_price > hhll_short[Table.Study.VALUE]:
                        self.__signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, settle_price))

                elif sma_short < sma_long:
                    if settle_price < hhll_short[Table.Study.VALUE_2]:
                        self.__signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, settle_price))

    def __generate_orders(self, date):
        """
        Generate Orders from Signals

        :param date:    date for the market open
        """
        orders = []

        for signal in self.__signals:
            market = signal.market()

            if market.has_data(date):
                market_data = market.data(end_date=date)
                atr_long = market.study(Study.ATR_LONG, date)[-1][Table.Study.VALUE]
                open_price = market_data[-1][Table.Market.OPEN_PRICE]
                enter_signals = [s for s in self.__signals if s.type() == SignalType.ENTER]
                exit_signals = [s for s in self.__signals if s.type() == SignalType.EXIT]
                roll_signals = [s for s in self.__signals if s.type() == SignalType.ROLL_ENTER or s.type() == SignalType.ROLL_EXIT]
                market_position = self.__portfolio.market_position(market)

                if market_position and (signal in exit_signals or signal in roll_signals):
                    orders.append(Order(market, signal, date, open_price, market_position.quantity()))

                if market_position is None and signal in enter_signals:
                    quantity = self.__risk.position_size(market.point_value(), market.currency(), atr_long, date)
                    # TODO keep track of signal that don't pass
                    if quantity:
                        orders.append(Order(market, signal, date, open_price, quantity))

        return orders

    def __transfer_orders(self, orders):
        """
        Transfer orders to broker

        :param orders:  list of order objects
        """
        for order in orders:
            order_result = self.__broker.transfer(order)

            if order_result.type() == OrderResultType.FILLED:
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
