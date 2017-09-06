#!/usr/bin/python

import sys
import calendar
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
        day = start_date
        previous_day = start_date
        days = Timer.daily_date_range(start_date, end_date)
        length = len(days)
        # TODO filter by major holidays in major exchanges
        for i, day in enumerate(days):
            self.__log(day, i, length)
            self.dispatch(EventType.MARKET_OPEN, day, previous_day)  # execute orders
            self.dispatch(EventType.MARKET_CLOSE, day, previous_day)  # accounting
            self.dispatch(EventType.EOD_DATA, day, previous_day)  # calculate studies and signals
            previous_day = day

        self.__log(day, complete=True)
        self.dispatch(EventType.COMPLETE, day)

    @staticmethod
    def daily_date_range(start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Construct and return range of daily dates from start date to end date passed in, included

        :param start_date:  start date of range
        :param end_date:    end date of range
        :return:            list fo date objects
        """
        workdays = range(1, 6)
        return [start_date + dt.timedelta(days=i) for i in xrange(0, (end_date - start_date).days + 1)
                if (start_date + dt.timedelta(days=i)).isoweekday() in workdays]

    @staticmethod
    def monthly_date_range(start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Construct and return range of dates in monthly interval
        in between the starting and ending dates passed in included

        :param start_date:  start date
        :param end_date:    end date
        :return:            list of date objects
        """
        dates = [dt.date(year, month, calendar.monthrange(year, month)[1])
                 for year in range(start_date.year, end_date.year + 1)
                 for month in range(1, 13)]

        return [d for d in dates if start_date < d < end_date] + [end_date]

    @staticmethod
    def yearly_date_range(start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Construct and return range of dates in yearly interval
        in between the starting and ending dates passed in included

        :param start_date:  start date
        :param end_date:    end date
        :return:            list of date objects
        """
        return [dt.date(year, 12, calendar.monthrange(year, 12)[1]) for year in range(start_date.year, end_date.year + 1)]

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
