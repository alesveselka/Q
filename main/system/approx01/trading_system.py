#!/usr/bin/python

import datetime
from enum import Study
from enum import EventType
from enum import Direction
from strategy_signal import Signal
from position import Position
from event_dispatcher import EventDispatcher


class TradingSystem(EventDispatcher):

    def __init__(self, investment_universe):
        super(TradingSystem, self).__init__()

        self.__investment_universe = investment_universe

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
            last_date = market_data[-1][1]  # TODO not actual dates from records, but from iterator!
            delta = last_date - start_date

            # TODO don't need Market to create them
            sma_100 = m.study(Study.SMA, market_data, long_window)
            sma_50 = m.study(Study.SMA, market_data, short_window)
            hhll_100 = m.study(Study.HHLL, market_data, long_window)
            hhll_50 = m.study(Study.HHLL, market_data, short_window)
            atr = m.study(Study.ATR, market_data, long_window)

            # TODO not actual dates from records, but from iterator!
            # TODO implement custom iterator over the data dates?
            for date in (start_date + datetime.timedelta(n) for n in range(delta.days+1)):
                data_window = m.data(start_date, date)

                if len(data_window) >= long_window + 1:  # querying '-2' index, because I need one more record
                    # print 'Processing %s from %s to %s' % (m.code(), start_date, date)

                    sma_100_lookup = [s for s in sma_100 if data_window[-2][1] <= s[0] <= date]
                    sma_50_lookup = [s for s in sma_50 if data_window[-2][1] <= s[0] <= date]
                    hhll_lookup = [s for s in hhll_50 if data_window[-2][1] <= s[0] <= date]
                    atr_lookup = [s for s in atr if data_window[-2][1] <= s[0] <= date]
                    last_price = data_window[-1][5]
                    market_positions = [p for p in positions if p.code() == m.code()]
                    signal = None

                    """
                    Exit Positions
                    """
                    if len(market_positions):
                        position = positions[0]
                        hl = [h for h in hhll_100 if h[0] == date]
                        if len(hl):  # TODO if date represent actual date from records, the 'if' will not be necessary
                            if position.direction() == Direction.LONG:
                                stop_loss = hl[0][1] - 3 * atr_lookup[-1][1]
                                if last_price <= stop_loss:
                                    print 'EXIT!', date
                                    positions.remove(position)
                            elif position.direction() == Direction.SHORT:
                                stop_loss = hl[0][2] + 3 * atr_lookup[-1][1]
                                if last_price >= stop_loss:
                                    print 'EXIT!', date
                                    positions.remove(position)

                    """
                    Signals
                    """
                    if sma_50_lookup[-2][1] > sma_100_lookup[-2][1]:
                        if last_price > hhll_lookup[-2][1]:
                            # TODO 'code' is not the actual instrument code, but general market code
                            signal = Signal(m.code(), Direction.LONG, date, last_price)

                    elif sma_50_lookup[-2][1] < sma_100_lookup[-2][1]:
                        if last_price < hhll_lookup[-2][2]:
                            # TODO 'code' is not the actual instrument code, but general market code
                            signal = Signal(m.code(), Direction.SHORT, date, last_price)

                    """
                    Open Positions (Position Candidate)
                    """
                    # TODO also check if there IS position, but in opposite direction!
                    if not len(market_positions) and signal:
                        print 'appending ', Position(signal, 1)
                        positions.append(Position(signal, 1))  # TODO enter day will be signal date + 1 (opened next day)

        # for signal in signals:
        #     market = [m for m in markets if m.code() == signal.code()][0]
        #     market_data = market.data(start_date, today)
        #
        #     atr = market.study(Study.ATR, market_data, short_window)
        #
        #     print signal
        #
        #     if len([p for p in positions if p.code() == signal.code()]):
        #         # TODO check SL
        #         data_window = market.data(start_date, date)
        #         atr_lookup = [s for s in atr if data_window[-2][1] <= s[0] <= date]
        #     else:
        #         print 'appending ', Position(signal, 1)
        #         positions.append(Position(signal, 1))
