#!/usr/bin/python

import datetime
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


class TradingSystem(EventDispatcher):

    def __init__(self, investment_universe, risk, account, portfolio, broker):
        super(TradingSystem, self).__init__()

        self.__investment_universe = investment_universe
        self.__risk = risk
        self.__account = account
        self.__portfolio = portfolio
        self.__broker = broker

        self.__subscribe()

    def __subscribe(self):
        self.__investment_universe.on(EventType.MARKET_DATA, self.__on_market_data)

    def __on_market_data(self, data):
        # TODO pass in the configuration of parameters
        short_window = 50
        long_window = 100
        markets = data[0]
        # start_date = data[1]
        start_date = datetime.date(2016, 1, 1)
        now = datetime.datetime.now()
        today = datetime.date(now.year, now.month, now.day)
        # today = datetime.date(2016, 10, 1)

        print '_on_market_data:', len(markets), start_date, today

        signals = []
        positions = []
        trades = []

        # TODO Parallel?!
        for m in markets:
            market_data = m.data(start_date, today)
            last_price = 0

            # TODO don't need Market to create them
            sma_long = m.study(Study.SMA, market_data, long_window)
            sma_short = m.study(Study.SMA, market_data, short_window)
            hhll_long = m.study(Study.HHLL, market_data, long_window)
            hhll_short = m.study(Study.HHLL, market_data, short_window)
            atr = m.study(Study.ATR, market_data, long_window)
            atr_short = m.study(Study.ATR, market_data, short_window)
            volume_sma = SMA([(d[1], d[6]) for d in market_data], short_window)

            for date in [d[1] for d in market_data]:
                data_window = m.data(start_date, date)

                if len(data_window) >= long_window + 1:  # querying '-2' index, because I need one more record
                    # print 'Processing %s from %s to %s' % (m.code(), start_date, date)

                    """
                    Studies
                    """
                    sma_long_lookup = [s for s in sma_long if data_window[-2][1] <= s[0] <= date]
                    sma_short_lookup = [s for s in sma_short if data_window[-2][1] <= s[0] <= date]
                    hhll_lookup = [s for s in hhll_short if data_window[-2][1] <= s[0] <= date]
                    atr_lookup = [s for s in atr if data_window[-2][1] <= s[0] <= date]
                    atr_short_lookup = [s for s in atr_short if data_window[-2][1] <= s[0] <= date]
                    volume_lookup = [s for s in volume_sma if data_window[-2][1] <= s[0] <= date]
                    previous_last_price = last_price
                    open_price = data_window[-1][2]
                    last_price = data_window[-1][5]
                    open_signals = [s for s in signals if s.type() == SignalType.ENTER]
                    close_signals = [s for s in signals if s.type() == SignalType.EXIT]
                    market_positions = [p for p in self.__portfolio.positions() if p.market().code() == m.code()]

                    self.__broker.update_margin_loans(date, previous_last_price)  # TODO sync via events

                    """
                    Close Positions
                    """
                    if len(close_signals) and len(market_positions):
                        for signal in close_signals:
                            for position in [p for p in market_positions if p.market().code() == signal.market().code()]:
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
                    if len(open_signals) and not len(market_positions):
                        for signal in open_signals:
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
                                result = self.__broker.transfer(order, m.margin(previous_last_price))  # TODO convert FX (On Broker side?)

                                # print 'Open ', position, result.price()
                            else:
                                print 'Too low of quantity! Can\'t afford it.', quantity

                    """
                    Close Signals
                    """
                    del signals[:]

                    if len(market_positions):
                        for position in market_positions:
                            hl = [h for h in hhll_long if h[0] == date]

                            if position.direction() == Direction.LONG:
                                stop_loss = hl[0][1] - 3 * atr_lookup[-1][1]
                                if last_price <= stop_loss:
                                    signals.append(Signal(m, SignalType.EXIT, Direction.SHORT, date, last_price))
                            elif position.direction() == Direction.SHORT:
                                stop_loss = hl[0][2] + 3 * atr_lookup[-1][1]
                                if last_price >= stop_loss:
                                    signals.append(Signal(m, SignalType.EXIT, Direction.LONG, date, last_price))

                    """
                    Open Signals
                    """
                    if sma_short_lookup[-2][1] > sma_long_lookup[-2][1]:
                        if last_price > hhll_lookup[-2][1]:
                            # TODO 'code' is not the actual instrument code, but general market code
                            signals.append(Signal(m, SignalType.ENTER, Direction.LONG, date, last_price))

                    elif sma_short_lookup[-2][1] < sma_long_lookup[-2][1]:
                        if last_price < hhll_lookup[-2][2]:
                            # TODO 'code' is not the actual instrument code, but general market code
                            signals.append(Signal(m, SignalType.ENTER, Direction.SHORT, date, last_price))

                    """
                    Mark-To-Market!!!
                    Open - Settlement || Settlement - Settlement || Settlement - Exit

                    Has Open Positions
                        New Transaction - Mark to Market non-base FX balance (MTM amount is available next day!)
                        New Transaction - Mark to Market PnL

                        Interest on FX debit (Margin Loan)

                    Has new Signals
                        Available Funds? (+ commissions)
                            Instrument NOT in base currency?
                                Convert by current rate

                        New Transaction - Margin Loan

                        New Transaction - open position
                        New Transaction - substract commission
                    """

                    # TODO mark to market non-base FX balances
                    self.__broker.mark_to_market(date)  # TODO sync via events
                    # TODO apply interest

                    # TODO interests

        total = 0.0
        commissions = 0.0
        slippage = Decimal(0.0)
        print ('-' * 10), 'trades', ('-' * 10)
        for t in trades:
            print t
            total += float(t.result() * Decimal(t.quantity()) * t.market().point_value())
            commissions += t.commissions()
            slippage += t.slippage()

        print 'Total $ %s in %s trades (commissions: %.2f, slippage: %.2f(%.2f))' % (
            total,
            len(trades),
            commissions,
            slippage,
            float(slippage * t.market().point_value())
        )
        print 'Equity: %.2f, funds: %.2f' % (self.__account.equity(), self.__account.available_funds())
