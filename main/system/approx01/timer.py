#!/usr/bin/python

import sys
import datetime as dt
from enum import EventType
from event_dispatcher import EventDispatcher


class Timer(EventDispatcher):

    def __init__(self):
        super(Timer, self).__init__()

    def start(self, start_date=dt.date(1990, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Start the strategy and iterates through the day range, notifying subscribers

        :param start_date:  Start date of the strategy
        :param end_date:    End date of the strategy
        """
        workdays = range(1, 6)
        day = start_date
        previous_day = start_date
        days = xrange(0, (end_date - start_date).days + 1)
        length = len(days)

        for i in days:
            day = start_date + dt.timedelta(days=i)
            if day.isoweekday() in workdays:
                self.__log(day, i, length)
                self.dispatch(EventType.MARKET_OPEN, day, previous_day)  # execute orders
                self.dispatch(EventType.MARKET_CLOSE, day, previous_day)  # accounting
                self.dispatch(EventType.EOD_DATA, day, previous_day)  # calculate studies and signals
                previous_day = day

        self.__log(day, complete=True)
        self.dispatch(EventType.COMPLETE, day)

    def __log(self, day, index=0, length=0.0, complete=False):
        """
        Print message and percentage progress to console

        :param index:       Index of the item being processed
        :param length:      Length of the whole range
        :param complete:    Flag indicating if the progress is complete
        """
        sys.stdout.write('%s\r' % (' ' * 80))
        if complete:
            sys.stdout.write('Strategy progress complete\r\n')
        else:
            sys.stdout.write('Strategy progress ... %s (%d of %d) [%d %%]\r' % (
                day,
                index,
                length,
                float(index) / length * 100
            ))
        sys.stdout.flush()
