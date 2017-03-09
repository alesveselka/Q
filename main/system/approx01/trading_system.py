#!/usr/bin/python

import datetime
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

        for m in markets:
            market_data = m.data(start_date, today)
            last_date = market_data[-1][1]  # TODO not actual dates from records, but from iterator!
            delta = last_date - start_date

            for date in (start_date + datetime.timedelta(n) for n in range(delta.days)):
                data_window = m.data(start_date, date)

                if len(data_window) >= long_window:
                    print 'Processing %s from %s to %s' % (m.code(), start_date, date)

                    sma_100 = m.study(Study.SMA, data_window, long_window)
                    sma_50 = m.study(Study.SMA, data_window, short_window)
                    hhll = m.study(Study.HHLL, data_window, short_window)

                    # TODO remove hard-coded values (5=Settle, etc.)
                    if data_window[-1][5] > hhll[-2][1]:
                        if sma_50[-2][1] > sma_100[-2][1]:
                            # TODO check if Long position has not already exist
                            print 'LONG!'

                    if data_window[-1][5] < hhll[-2][2]:
                        if sma_50[-2][1] < sma_100[-2][1]:
                            # TODO check if Short position has not already exist
                            print 'SHORT!'
