#!/usr/bin/python

import datetime as dt
from enum import EventType
from event_dispatcher import EventDispatcher


class Timer(EventDispatcher):

    def __init__(self):
        super(Timer, self).__init__()

    def start(self, start_date=dt.date(1990, 1, 1), end_date=dt.date(9999, 12, 31)):
        workdays = range(1, 6)
        day = start_date
        previous_day = start_date

        for i in xrange(0, (end_date - start_date).days + 1):
            day = start_date + dt.timedelta(days=i)
            if day.isoweekday() in workdays:
                # print '%s [%s] %s (previous %s) %s' % (('-' * 40), i, day, previous_day, ('-' * 40))
                self.dispatch(EventType.MARKET_OPEN, day, previous_day)  # execute orders
                self.dispatch(EventType.MARKET_CLOSE, day, previous_day)  # accounting
                self.dispatch(EventType.EOD_DATA, day, previous_day)  # calculate studies and signals
                previous_day = day

        self.dispatch(EventType.COMPLETE, day)
