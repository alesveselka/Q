#!/usr/bin/python

import datetime
from math import floor
from decimal import Decimal
from enum import Study
from enum import EventType
from enum import Direction
from enum import SignalType
from enum import OrderType
from enum import TransactionType
from strategy_signal import Signal
from position import Position
from transaction import Transaction
from order import Order
from trade import Trade
from risk import Risk
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
        short_window = 50
        long_window = 100
        markets = data[0]
        start_date = data[1]
        now = datetime.datetime.now()
        today = datetime.date(now.year, now.month, now.day)

        print '_on_market_data:', len(markets), start_date, today

        signals = []
        positions = []
        trades = []

        # TODO Parallel?!
        for m in markets:
            market_data = m.data(start_date, today)

            # TODO don't need Market to create them
            sma_long = m.study(Study.SMA, market_data, long_window)
            sma_short = m.study(Study.SMA, market_data, short_window)
            hhll_long = m.study(Study.HHLL, market_data, long_window)
            hhll_short = m.study(Study.HHLL, market_data, short_window)
            atr = m.study(Study.ATR, market_data, long_window)
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
                    open_price = data_window[-1][2]
                    last_price = data_window[-1][5]
                    open_signals = [s for s in signals if s.type() == SignalType.OPEN]
                    close_signals = [s for s in signals if s.type() == SignalType.CLOSE]
                    market_positions = [p for p in positions if p.market().code() == m.code()]

                    # TODO re-calculate margins

                    """
                    Close Positions
                    """
                    if len(close_signals) and len(market_positions):
                        for signal in close_signals:
                            for position in [p for p in market_positions if p.market().code() == signal.market().code()]:
                                print 'Close ', Position(position.market(), position.direction(), date, open_price, position.quantity())
                                print 'Realized via MTM: ', position.mark_to_market(date, open_price), position.pnl()

                                order = Order(m, {
                                                  Direction.LONG: OrderType.BUY,
                                                  Direction.SHORT: OrderType.SELL
                                              }.get(signal.direction()),
                                              date,
                                              open_price,
                                              position.quantity()
                                              )
                                self.__broker.transfer(order)

                                positions.remove(position)
                                trades.append(Trade(
                                    position.market(),
                                    position.direction(),
                                    position.quantity(),
                                    position.date(),
                                    position.price(),
                                    date,
                                    open_price
                                ))

                    """
                    Open Positions
                    """
                    if len(open_signals) and not len(market_positions):
                        for signal in open_signals:
                            # TODO convert non-base-currency point_value to the base-currency value!
                            quantity = (self.__risk.position_sizing() * self.__account.equity()) / float(atr_lookup[-1][1] * m.point_value())

                            # TODO if 'quantity < 1.0' I can't afford it
                            if floor(quantity):
                                position = Position(m, signal.direction(), date, open_price, floor(quantity))
                                # TODO move to its own 'operation' object?
                                order = Order(m, {
                                        Direction.LONG: OrderType.BUY,
                                        Direction.SHORT: OrderType.SELL
                                    }.get(signal.direction()),
                                    date,
                                    open_price,
                                    floor(quantity)
                                )
                                self.__broker.transfer(order)

                                # print 'Open ', position
                                # TODO oder can be rejected and thus result in no new position!
                                positions.append(position)
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
                                    signals.append(Signal(m, SignalType.CLOSE, Direction.SHORT, date, last_price))
                            elif position.direction() == Direction.SHORT:
                                stop_loss = hl[0][2] + 3 * atr_lookup[-1][1]
                                if last_price >= stop_loss:
                                    signals.append(Signal(m, SignalType.CLOSE, Direction.LONG, date, last_price))

                    """
                    Open Signals
                    """
                    if sma_short_lookup[-2][1] > sma_long_lookup[-2][1]:
                        if last_price > hhll_lookup[-2][1]:
                            # TODO 'code' is not the actual instrument code, but general market code
                            signals.append(Signal(m, SignalType.OPEN, Direction.LONG, date, last_price))

                    elif sma_short_lookup[-2][1] < sma_long_lookup[-2][1]:
                        if last_price < hhll_lookup[-2][2]:
                            # TODO 'code' is not the actual instrument code, but general market code
                            signals.append(Signal(m, SignalType.OPEN, Direction.SHORT, date, last_price))

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
                    # self.__broker.mark_to_market(m, data_window[-2][5], data_window[-1][5])  # TODO synchronize via events

                    for p in self.__portfolio.positions():
                    # for p in positions:
                        if p.market() == m:  # TODO compare by IDs?
                            diff = p.mark_to_market(date, last_price)

                            # TODO do I need 'quantity' in this type of transaction?
                            transaction = Transaction(m, TransactionType.MTM, date, diff, p.quantity(), 0)
                            self.__account.add_transaction(transaction)

                    # TODO interests

        total = 0
        for t in trades:
            print t
            total += float(t.result() * Decimal(t.quantity()) * t.market().point_value())

        print 'Total $ %s in %s trades' % (total, len(trades))
