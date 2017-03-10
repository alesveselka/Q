#!/usr/bin/python

import datetime
import time
from enum import Study
from enum import EventType
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

        print '_on_market_data:', len(markets), start_date

        # TODO Parallel?!
        for m in markets:
            market_data = m.data(start_date, today)
            last_date = market_data[-1][1]  # TODO not actual dates from records, but from iterator!
            delta = last_date - start_date

            lookup_date = market_data[int(len(market_data) / 4)][1]
            print 'Lookup date: %s' % lookup_date

            t0 = time.time()
            sma_100 = m.study(Study.SMA, market_data, long_window)
            sma_50 = m.study(Study.SMA, market_data, short_window)
            # print 'SMA, time: ', (time.time() - t0), len(sma_100)

            t0 = time.time()
            ema = m.study(Study.EMA, market_data, short_window)
            # print 'EMA, time: %s' % (time.time() - t0)

            t0 = time.time()
            hhll = m.study(Study.HHLL, market_data, short_window)
            # print 'HHLL, time: %s' % (time.time() - t0)

            t0 = time.time()
            atr = m.study(Study.ATR, market_data, short_window)
            # print 'ATR, time: %s' % (time.time() - t0)

            # t0 = time.time()
            # sma_lookup = [s for s in sma_100 if s[0] == lookup_date]
            # print 'SMA lookup: %s, time: %s' % (sma_lookup, time.time() - t0)
            #
            # t0 = time.time()
            # ema_lookup = [e for e in ema if e[0] == lookup_date]
            # print 'EMA lookup: %s, time: %s' % (ema_lookup, time.time() - t0)
            #
            # t0 = time.time()
            # hhll_lookup = [e for e in hhll if e[0] == lookup_date]
            # print 'HHLL lookup: %s, time: %s' % (ema_lookup, time.time() - t0)
            #
            # t0 = time.time()
            # atr_lookup = [e for e in atr if e[0] == lookup_date]
            # print 'ATR lookup: %s, time: %s' % (atr_lookup, time.time() - t0)



            for date in (start_date + datetime.timedelta(n) for n in range(delta.days+1)):
                data_window = m.data(start_date, date)

                if len(data_window) >= long_window + 1:  # querying '-2' index, so I need one more record
                    print 'Processing %s from %s to %s' % (m.code(), start_date, date)

                    # TODO calculate up-front from all data and then use just cached values (if date lookup is faster than calculation ... ?)
                    # sma_100 = m.study(Study.SMA, data_window, long_window)
                    # sma_50 = m.study(Study.SMA, data_window, short_window)
                    # hhll = m.study(Study.HHLL, data_window, short_window)
                    # atr = m.study(Study.ATR, data_window, short_window)
                    # print data_window[-2][1], sma_100[0], date
                    sma_100_lookup = [s for s in sma_100 if data_window[-2][1] <= s[0] <= date]
                    sma_50_lookup = [s for s in sma_50 if data_window[-2][1] <= s[0] <= date]
                    ema_lookup = [s for s in ema if data_window[-2][1] <= s[0] <= date]
                    hhll_lookup = [s for s in hhll if data_window[-2][1] <= s[0] <= date]
                    atr_lookup = [s for s in atr if data_window[-2][1] <= s[0] <= date]

                    # TODO remove hard-coded values (5=Settle, etc.)
                    if data_window[-1][5] > hhll_lookup[-2][1]:
                        if sma_50_lookup[-2][1] > sma_100_lookup[-2][1]:
                            # TODO check if Long position has not already exist
                            print 'LONG!'

                    if data_window[-1][5] < hhll_lookup[-2][2]:
                        if sma_50_lookup[-2][1] < sma_100_lookup[-2][1]:
                            # TODO check if Short position has not already exist
                            print 'SHORT!'

                    # # TODO remove hard-coded values (5=Settle, etc.)
                    # if data_window[-1][5] > hhll[-2][1]:
                    #     if sma_50[-2][1] > sma_100[-2][1]:
                    #         # TODO check if Long position has not already exist
                    #         print 'LONG!'
                    #
                    # if data_window[-1][5] < hhll[-2][2]:
                    #     if sma_50[-2][1] < sma_100[-2][1]:
                    #         # TODO check if Short position has not already exist
                    #         print 'SHORT!'
