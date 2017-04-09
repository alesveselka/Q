#!/usr/bin/python

from math import floor
from decimal import Decimal
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

    def subscribe(self):
        self.__timer.on(EventType.EOD_DATA, self.__on_eod_data)
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)

    def __on_market_open(self, date, previous_date):
        print EventType.MARKET_OPEN, date, previous_date, len(self.__signals)

        for signal in self.__signals:
            m = signal.market()
            market_data = m.data(end_date=date)

            if market_data[-1][1] == date:  # TODO do not even call if there the date is not trading date

                """
                Studies
                """
                atr_long = m.study(Study.ATR_LONG, date)[-1][1]
                atr_short = m.study(Study.ATR_SHORT, date)[-1][1]
                volume_short = m.study(Study.VOL_SHORT, date)[-1][1]
                open_price = market_data[-1][2]
                previous_last_price = market_data[-2][5]
                open_signals = [s for s in self.__signals if s.type() == SignalType.ENTER]
                close_signals = [s for s in self.__signals if s.type() == SignalType.EXIT]
                market_positions = [p for p in self.__portfolio.positions() if p.market().code() == m.code()]

                """
                Close Positions
                """
                if signal in close_signals and len(market_positions):
                    for position in market_positions:
                        order_result = self.__broker.transfer(Order(
                                m,
                                self.__order_type(signal.type(), signal.direction()),
                                date,
                                open_price,
                                position.quantity(),
                                atr_short,
                                volume_short
                            ), m.margin(previous_last_price) * position.quantity())

                        # TODO move to broker?
                        self.__trades.append(Trade(
                            position.market(),
                            position.direction(),
                            position.quantity(),
                            position.date(),
                            position.price(),
                            abs(position.order_price() - position.price()),
                            date,
                            order_result.price(),
                            abs(order_result.price() - open_price),
                            order_result.commission() * 2
                        ))

                """
                Open Positions
                """
                # if len(open_signals) and not len(market_positions):
                if signal in open_signals and not len(market_positions):
                    # for signal in open_signals:
                    quantity = self.__risk.position_size(m.point_value(), m.currency(), atr_long)

                    # TODO if 'quantity < 1.0' I can't afford it
                    if quantity:
                        order_result = self.__broker.transfer(Order(
                            m,
                            self.__order_type(signal.type(), signal.direction()),
                            date,
                            open_price,
                            quantity,
                            atr_short,
                            volume_short
                        ), m.margin(previous_last_price) * quantity)

                    else:
                        print 'Too low of quantity! Can\'t afford it.', quantity

        del self.__signals[:]

    def __on_market_close(self, date, previous_date):
        pass

    def __on_eod_data(self, date, previous_date):
        print EventType.EOD_DATA, date, previous_date

        # TODO pass in the configuration of parameters
        short_window = 50
        long_window = 100

        # TODO Parallel?!
        for m in self.__markets:
            market_data = m.data(end_date=date)

            # TODO replace hard-coded data
            if len(market_data) >= long_window + 1 and market_data[-1][1] == date:

                """
                Studies
                """
                sma_long = m.study(Study.SMA_LONG, date)[-2][1]
                sma_short = m.study(Study.SMA_SHORT, date)[-2][1]
                hhll_long = m.study(Study.HHLL_LONG, date)
                hhll_short = m.study(Study.HHLL_SHORT, date)
                atr_long = m.study(Study.ATR_LONG, date)[-1][1]
                last_price = market_data[-1][5]
                market_positions = [p for p in self.__portfolio.positions() if p.market().code() == m.code()]

                """
                Close Signals
                """
                if len(market_positions):
                    for position in market_positions:
                        print 'position: ', position
                        if position.direction() == Direction.LONG:
                            stop_loss = hhll_long[-1][1] - 3 * atr_long
                            if last_price <= stop_loss:
                                self.__signals.append(Signal(m, SignalType.EXIT, Direction.SHORT, date, last_price))
                        elif position.direction() == Direction.SHORT:
                            stop_loss = hhll_long[-1][2] + 3 * atr_long
                            if last_price >= stop_loss:
                                self.__signals.append(Signal(m, SignalType.EXIT, Direction.LONG, date, last_price))

                """
                Open Signals
                """
                if sma_short > sma_long:
                    if last_price > hhll_short[-2][1]:
                        # TODO 'code' is not the actual instrument code, but general market code
                        self.__signals.append(Signal(m, SignalType.ENTER, Direction.LONG, date, last_price))

                elif sma_short < sma_long:
                    if last_price < hhll_short[-2][2]:
                        # TODO 'code' is not the actual instrument code, but general market code
                        self.__signals.append(Signal(m, SignalType.ENTER, Direction.SHORT, date, last_price))

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
