#!/usr/bin/python

from enum import Study
from enum import EventType
from enum import Direction
from enum import SignalType
from enum import OrderType
from enum import Table
from strategy_signal import Signal
from order import Order
from trade import Trade


class TradingSystem:

    def __init__(self, timer, markets, risk, portfolio, broker):
        self.__timer = timer
        self.__markets = markets
        self.__risk = risk
        self.__portfolio = portfolio
        self.__broker = broker
        self.__signals = []
        self.__trades = []

    def trades(self):
        """
        Return trades

        :return: list of Trade objects
        """
        return self.__trades

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

                sma_long = market.study(Study.SMA_LONG, date)[-2][Table.Study.VALUE]
                sma_short = market.study(Study.SMA_SHORT, date)[-2][Table.Study.VALUE]
                hhll_long = market.study(Study.HHLL_LONG, date)
                hhll_short = market.study(Study.HHLL_SHORT, date)
                atr_long = market.study(Study.ATR_LONG, date)[-1][Table.Study.VALUE]
                settle_price = market_data[-1][Table.Market.SETTLE_PRICE]
                market_position = self.__portfolio.market_position(market)

                # TODO pass in rules
                if market_position:
                    direction = market_position.direction()
                    if direction == Direction.LONG:
                        # TODO move SL to Risk object?
                        stop_loss = hhll_long[-1][Table.Study.VALUE] - 3 * atr_long
                        if settle_price <= stop_loss:
                            self.__signals.append(Signal(market, SignalType.EXIT, Direction.SHORT, date, settle_price))
                    elif direction == Direction.SHORT:
                        # TODO move SL to Risk object?
                        stop_loss = hhll_long[-1][Table.Study.VALUE_2] + 3 * atr_long
                        if settle_price >= stop_loss:
                            self.__signals.append(Signal(market, SignalType.EXIT, Direction.LONG, date, settle_price))

                    # Naive contract roll implementation (end of each month)
                    if date.month > previous_date.month and len(self.__signals) == 0:
                        opposite_direction = Direction.LONG if direction == Direction.SHORT else Direction.LONG
                        self.__signals.append(Signal(market, SignalType.ROLL_EXIT, opposite_direction, date, settle_price))
                        self.__signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, settle_price))

                # TODO pass-in rules
                if sma_short > sma_long:
                    if settle_price > hhll_short[-2][Table.Study.VALUE]:
                        self.__signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, settle_price))

                elif sma_short < sma_long:
                    if settle_price < hhll_short[-2][Table.Study.VALUE_2]:
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
                order_type = self.__order_type(signal.type(), signal.direction())

                if market_position and (signal in exit_signals or signal in roll_signals):
                    orders.append(Order(market, order_type, date, open_price, market_position.quantity()))

                if market_position is None and signal in enter_signals:
                    quantity = self.__risk.position_size(market.point_value(), market.currency(), atr_long, date)
                    if quantity:
                        orders.append(Order(market, order_type, date, open_price, quantity))

        return orders

    def __transfer_orders(self, orders):
        """
        Transfer orders to broker

        :param orders:  list of order objects
        """
        for order in orders:
            # TODO temporal binding - identify the position better way
            market_position = self.__portfolio.market_position(order.market())
            order_result = self.__broker.transfer(order)

            if order.type() == OrderType.BTC or order.type() == OrderType.STC:
                self.__trades.append(Trade(market_position, order, order_result))

    def __order_type(self, signal_type, signal_direction):
        """
        Return OrderType based on signal type and direction passed in

        :param signal_type:         Signal type, either ENTER of EXIT
        :param signal_direction:    Signal direction, either LONG or SHORT
        :return:                    string - OrderType
        """
        return {
            SignalType.ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.EXIT: {Direction.LONG: OrderType.BTC, Direction.SHORT: OrderType.STC},
            SignalType.ROLL_ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.ROLL_EXIT: {Direction.LONG: OrderType.BTC, Direction.SHORT: OrderType.STC}
        }.get(signal_type).get(signal_direction)
