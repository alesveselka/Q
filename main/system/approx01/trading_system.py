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

    def subscribe(self):
        self.__timer.on(EventType.EOD_DATA, self.__on_eod_data)
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)

    def __on_market_open(self, date, previous_date):
        print '__on_market_open', date, previous_date, len(self.__signals)

        trades = []

        for signal in self.__signals:
            m = signal.market()
            market_data = m.data(end_date=date)

            if market_data[-1][1] == date:

                print date, m.code(), len(market_data)

                """
                Studies
                """
                atr_lookup = m.study(Study.ATR_LONG, date)
                atr_short_lookup = m.study(Study.ATR_SHORT, date)
                volume_lookup = m.study(Study.VOL_SHORT, date)
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
                        # print 'Close ', Position(position.market(), position.direction(), date, open_price, position.quantity())

                        order = Order(m, {
                                Direction.LONG: OrderType.BTC,
                                Direction.SHORT: OrderType.STC
                            }.get(signal.direction()),
                            date,
                            open_price,
                            position.quantity(),
                            atr_short_lookup[-1][1],
                            volume_lookup[-1][1]
                        )
                        result = self.__broker.transfer(order, m.margin(previous_last_price) * position.quantity())

                        # TODO move to broker?
                        trades.append(Trade(
                            position.market(),
                            position.direction(),
                            position.quantity(),
                            position.date(),
                            position.price(),
                            abs(position.order_price() - position.price()),
                            date,
                            result.price(),
                            abs(result.price() - open_price),
                            result.commission() * 2
                        ))

                """
                Open Positions
                """
                # if len(open_signals) and not len(market_positions):
                if signal in open_signals and not len(market_positions):
                    # for signal in open_signals:
                    quantity = self.__risk.position_size(m.point_value(), m.currency(), atr_lookup[-1][1])

                    # TODO if 'quantity < 1.0' I can't afford it
                    if quantity:
                        # TODO move to its own 'operation' object?
                        order = Order(m, {
                            Direction.LONG: OrderType.BTO,
                            Direction.SHORT: OrderType.STO
                        }.get(signal.direction()),
                                      date,
                                      open_price,
                                      quantity,
                                      atr_short_lookup[-1][1],
                                      volume_lookup[-1][1]
                                      )
                        print order
                        result = self.__broker.transfer(order, m.margin(previous_last_price) * quantity)

                        # print 'Open ', position, result.price()
                    else:
                        print 'Too low of quantity! Can\'t afford it.', quantity

        del self.__signals[:]

    def __on_market_close(self, date, previous_date):
        pass

    def __on_eod_data(self, date, previous_date):
        print '__on_eod_data', date, previous_date

        # TODO pass in the configuration of parameters
        short_window = 50
        long_window = 100

        # TODO Parallel?!
        for m in self.__markets:
            market_data = m.data(end_date=date)

            # TODO replace hard-coded data
            if len(market_data) >= long_window + 1 and market_data[-1][1] == date:  # querying '-2' index, because I need one more record

                print date, m.code(), len(market_data)

                """
                Studies
                """
                sma_long_lookup = m.study(Study.SMA_LONG, date)
                sma_short_lookup = m.study(Study.SMA_SHORT, date)
                hhll_long_lookup = m.study(Study.HHLL_LONG, date)
                hhll_short_lookup = m.study(Study.HHLL_SHORT, date)
                atr_lookup = m.study(Study.ATR_LONG, date)
                last_price = market_data[-1][5]
                market_positions = [p for p in self.__portfolio.positions() if p.market().code() == m.code()]

                """
                Close Signals
                """
                if len(market_positions):
                    for position in market_positions:
                        hl = hhll_long_lookup[-1]
                        if position.direction() == Direction.LONG:
                            stop_loss = hl[1] - 3 * atr_lookup[-1][1]
                            if last_price <= stop_loss:
                                self.__signals.append(Signal(m, SignalType.EXIT, Direction.SHORT, date, last_price))
                        elif position.direction() == Direction.SHORT:
                            stop_loss = hl[2] + 3 * atr_lookup[-1][1]
                            if last_price >= stop_loss:
                                self.__signals.append(Signal(m, SignalType.EXIT, Direction.LONG, date, last_price))

                """
                Open Signals
                """
                if sma_short_lookup[-2][1] > sma_long_lookup[-2][1]:
                    if last_price > hhll_short_lookup[-2][1]:
                        # TODO 'code' is not the actual instrument code, but general market code
                        self.__signals.append(Signal(m, SignalType.ENTER, Direction.LONG, date, last_price))

                elif sma_short_lookup[-2][1] < sma_long_lookup[-2][1]:
                    if last_price < hhll_short_lookup[-2][2]:
                        # TODO 'code' is not the actual instrument code, but general market code
                        self.__signals.append(Signal(m, SignalType.ENTER, Direction.SHORT, date, last_price))

        # total = 0.0
        # commissions = 0.0
        # slippage = Decimal(0.0)
        # print ('-' * 10), 'trades', ('-' * 10)
        # for t in trades:
        #     print t
        #     total += float(t.result() * Decimal(t.quantity()) * t.market().point_value())
        #     commissions += t.commissions()
        #     slippage += t.slippage()
        #
        # print 'Total $ %s in %s trades (commissions: %.2f, slippage: %.2f(%.2f))' % (
        #     total,
        #     len(trades),
        #     commissions,
        #     slippage,
        #     float(slippage * t.market().point_value())
        # )
        # print 'Equity: %.2f, funds: %.2f' % (self.__account.equity(), self.__account.available_funds())
        # print 'Fx Balances: ', self.__account.to_fx_balance_string()
        # print 'Margin Balances: ', self.__account.to_margin_loans_string()
