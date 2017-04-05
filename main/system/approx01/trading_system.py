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
from study import SMA
from event_dispatcher import EventDispatcher


class TradingSystem(EventDispatcher):  # TODO do I need inherit from ED?

    def __init__(self, timer, markets, risk, account, portfolio, broker):
        super(TradingSystem, self).__init__()

        self.__timer = timer
        self.__markets = markets
        self.__risk = risk
        self.__account = account
        self.__portfolio = portfolio
        self.__broker = broker
        self.__signals = []

    def subscribe(self):
        self.__timer.on(EventType.EOD_DATA, self.__on_eod_data)
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)

    def __on_market_open(self, date, previous_date):
        print '__on_market_open', date, previous_date, len(self.__signals)
        # TODO pass in the configuration of parameters
        short_window = 50
        long_window = 100

        trades = []

        for signal in self.__signals:
            m = signal.market()
            market_data = m.data(end_date=date)

            if market_data[-1][1] == date:
                previous_date = market_data[-2][1]  # not used actually

                print date, m.code(), len(market_data)

                # TODO don't need Market to create them
                # TODO pre-calculate them during backtest?
                atr = m.study(Study.ATR, market_data, long_window)
                atr_short = m.study(Study.ATR, market_data, short_window)
                volume_sma = SMA([(d[1], d[6]) for d in market_data], short_window)

                """
                Studies
                """
                atr_lookup = [s for s in atr if market_data[-2][1] <= s[0] <= date]
                atr_short_lookup = [s for s in atr_short if market_data[-2][1] <= s[0] <= date]
                volume_lookup = [s for s in volume_sma if market_data[-2][1] <= s[0] <= date]
                open_price = market_data[-1][2]
                previous_last_price = market_data[-2][5]
                open_signals = [s for s in self.__signals if s.type() == SignalType.ENTER]
                close_signals = [s for s in self.__signals if s.type() == SignalType.EXIT]
                market_positions = [p for p in self.__portfolio.positions() if p.market().code() == m.code()]

                self.__broker.update_margin_loans(date, previous_last_price)  # TODO sync via events

                """
                Close Positions
                """
                # if len(close_signals) and len(market_positions):
                if signal in close_signals and len(market_positions):
                    # for signal in close_signals:
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
                        result = self.__broker.transfer(order, m.margin(previous_last_price))

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
                        # TODO once is position close, convert Fx P/L to base-currency

                """
                Open Positions
                """
                # if len(open_signals) and not len(market_positions):
                if signal in open_signals and not len(market_positions):
                    # for signal in open_signals:
                    # TODO move this calculation to Risk and remove 'account' dependency
                    quantity = (self.__risk.position_sizing() * self.__account.equity()) / \
                               Decimal(atr_lookup[-1][1] * self.__account.base_value(m.point_value(), m.currency()))

                    # TODO if 'quantity < 1.0' I can't afford it
                    if floor(quantity):
                        # TODO move to its own 'operation' object?
                        order = Order(m, {
                            Direction.LONG: OrderType.BTO,
                            Direction.SHORT: OrderType.STO
                        }.get(signal.direction()),
                                      date,
                                      open_price,
                                      floor(quantity),
                                      atr_short_lookup[-1][1],
                                      volume_lookup[-1][1]
                                      )
                        print order
                        result = self.__broker.transfer(order, m.margin(previous_last_price))

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
                previous_date = market_data[-2][1]  # not used actually

                print date, m.code(), len(market_data)

                # TODO don't need Market to create them
                # TODO pre-calculate them during backtest?
                sma_long = m.study(Study.SMA, market_data, long_window)
                sma_short = m.study(Study.SMA, market_data, short_window)
                hhll_long = m.study(Study.HHLL, market_data, long_window)
                hhll_short = m.study(Study.HHLL, market_data, short_window)
                atr = m.study(Study.ATR, market_data, long_window)

                """
                Studies
                """
                sma_long_lookup = [s for s in sma_long if s[0] <= date]
                sma_short_lookup = [s for s in sma_short if s[0] <= date]
                hhll_lookup = [s for s in hhll_short if s[0] <= date]
                atr_lookup = [s for s in atr if s[0] <= date]
                last_price = market_data[-1][5]
                previous_last_price = market_data[-2][5]
                market_positions = [p for p in self.__portfolio.positions() if p.market().code() == m.code()]

                self.__broker.update_margin_loans(date, previous_last_price)  # TODO sync via events

                """
                Close Signals
                """
                if len(market_positions):
                    for position in market_positions:
                        hl = [h for h in hhll_long if h[0] == date]
                        if position.direction() == Direction.LONG:
                            stop_loss = hl[0][1] - 3 * atr_lookup[-1][1]
                            if last_price <= stop_loss:
                                self.__signals.append(Signal(m, SignalType.EXIT, Direction.SHORT, date, last_price))
                        elif position.direction() == Direction.SHORT:
                            stop_loss = hl[0][2] + 3 * atr_lookup[-1][1]
                            if last_price >= stop_loss:
                                self.__signals.append(Signal(m, SignalType.EXIT, Direction.LONG, date, last_price))

                """
                Open Signals
                """
                if sma_short_lookup[-2][1] > sma_long_lookup[-2][1]:
                    if last_price > hhll_lookup[-2][1]:
                        # TODO 'code' is not the actual instrument code, but general market code
                        self.__signals.append(Signal(m, SignalType.ENTER, Direction.LONG, date, last_price))

                elif sma_short_lookup[-2][1] < sma_long_lookup[-2][1]:
                    if last_price < hhll_lookup[-2][2]:
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
