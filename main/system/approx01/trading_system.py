#!/usr/bin/python

from enum import Study
from enum import EventType
from enum import Direction
from enum import SignalType
from enum import OrderType
from strategy_signal import Signal
from order import Order
from trade import Trade
from event_dispatcher import EventDispatcher


class TradingSystem(EventDispatcher):  # TODO do I need inherit from ED?

    def __init__(self, timer, markets, risk, portfolio, broker):
        super(TradingSystem, self).__init__()

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
        # print EventType.MARKET_OPEN, date, previous_date

        self.__transfer_orders(self.__generate_orders(date))

        # TODO what if signals will be deleted on holiday and next day no orders created?
        del self.__signals[:]

    def __on_eod_data(self, date, previous_date):
        """
        End-of-Day event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # print EventType.EOD_DATA, date, previous_date

        self.__generate_signals(date, previous_date)

    def __generate_signals(self, date, previous_date):
        """
        Generate trading signals

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # print EventType.EOD_DATA, date, previous_date

        # TODO pass in the configuration of parameters
        short_window = 50
        long_window = 100

        for market in self.__markets:
            market_data = market.data(end_date=date)

            # TODO replace hard-coded data
            if len(market_data) >= long_window + 1 and market.has_data(date):

                sma_long = market.study(Study.SMA_LONG, date)[-2][1]
                sma_short = market.study(Study.SMA_SHORT, date)[-2][1]
                hhll_long = market.study(Study.HHLL_LONG, date)
                hhll_short = market.study(Study.HHLL_SHORT, date)
                atr_long = market.study(Study.ATR_LONG, date)[-1][1]
                last_price = market_data[-1][5]
                market_positions = self.__portfolio.positions_in_market(market)

                # TODO pass in rules
                if len(market_positions):
                    for position in market_positions:
                        if position.direction() == Direction.LONG:
                            stop_loss = hhll_long[-1][1] - 3 * atr_long
                            if last_price <= stop_loss:
                                self.__signals.append(Signal(market, SignalType.EXIT, Direction.SHORT, date, last_price))
                        elif position.direction() == Direction.SHORT:
                            stop_loss = hhll_long[-1][2] + 3 * atr_long
                            if last_price >= stop_loss:
                                self.__signals.append(Signal(market, SignalType.EXIT, Direction.LONG, date, last_price))

                # TODO pass-in rules
                if sma_short > sma_long:
                    if last_price > hhll_short[-2][1]:
                        self.__signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, last_price))

                elif sma_short < sma_long:
                    if last_price < hhll_short[-2][2]:
                        self.__signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, last_price))

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
                atr_long = market.study(Study.ATR_LONG, date)[-1][1]
                open_price = market_data[-1][2]
                open_signals = [s for s in self.__signals if s.type() == SignalType.ENTER]
                close_signals = [s for s in self.__signals if s.type() == SignalType.EXIT]
                positions = self.__portfolio.positions_in_market(market)
                order_type = self.__order_type(signal.type(), signal.direction())

                if signal in close_signals and len(positions):
                    for position in positions:
                        orders.append(Order(market, order_type, date, open_price, position.quantity()))

                if signal in open_signals and not len(positions):
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
            positions = self.__portfolio.positions_in_market(order.market())
            order_result = self.__broker.transfer(order)

            if order.type() == OrderType.BTC or order.type() == OrderType.STC:
                self.__trades.append(Trade(positions[0], order, order_result))

    def __order_type(self, signal_type, signal_direction):
        """
        Return OrderType based on signal type and direction passed in

        :param signal_type:         Signal type, either ENTER of EXIT
        :param signal_direction:    Signal direction, either LONG or SHORT
        :return:                    string - OrderType
        """
        return {
            SignalType.ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.EXIT: {Direction.LONG: OrderType.BTC, Direction.SHORT: OrderType.STC}
        }.get(signal_type).get(signal_direction)
