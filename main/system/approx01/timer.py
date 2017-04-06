#!/usr/bin/python

import time
import datetime as dt
from enum import EventType
from event_dispatcher import EventDispatcher


class Timer(EventDispatcher):

    def __init__(self):
        super(Timer, self).__init__()

    def start(self, start_data_date):
        workdays = range(1, 6)
        # start_data_date = dt.date(2017, 3, 20)
        now = dt.datetime.now()
        today = dt.date(now.year, now.month, now.day)
        # today = dt.date(2017, 4, 5)
        previous_day = start_data_date

        for i in xrange(0, (today - start_data_date).days + 1):
            day = start_data_date + dt.timedelta(days=i)
            if day.isoweekday() in workdays:
                print '%s [%s] %s (previous %s) %s' % (('-' * 40), i, day, previous_day, ('-' * 40))
                self.dispatch(EventType.MARKET_OPEN, day, previous_day)  # execute orders
                self.dispatch(EventType.MARKET_CLOSE, day, previous_day)  # accounting
                self.dispatch(EventType.EOD_DATA, day, previous_day)  # calculate studies and signals
                previous_day = day
