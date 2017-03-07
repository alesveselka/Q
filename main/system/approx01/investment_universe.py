#!/usr/bin/python

import datetime
from enum import EventType
from market import Market
from event_dispatcher import EventDispatcher


class InvestmentUniverse(EventDispatcher):

    def __init__(self, name, start_date, timer, connection):
        super(InvestmentUniverse, self).__init__()

        self.__name = name
        self.__start_date = start_date
        self.__timer = timer
        self.__connection = connection
        self.__markets = []

        self.__timer.on(EventType.HEARTBEAT, self.__on_timer_heartbeat)

    def __on_timer_heartbeat(self, *data):
        self.__load_markets()  # TODO load only when study is updated?
        self.__update_studies()

        now = datetime.datetime.now()
        today = datetime.date(now.year, now.month, now.day)
        delta = today - self.__start_date
        print delta

        # for date in (self.__start_date + datetime.timedelta(n) for n in range(delta.days)):
        #     print date, len([m for m in self.__markets if len(m.data(date))])

        self.dispatch(EventType.MARKET_DATA, self.__markets)

    def __market_ids(self, cursor):
        cursor.execute("SELECT market_ids FROM investment_universe WHERE name = '%s';" % self.__name)
        return cursor.fetchone()[0].split(',')[0]

    def __load_markets(self):
        cursor = self.__connection.cursor()
        sql = """
            SELECT m.name, m.code, m.data_codes, m.currency, m.first_data_date, g.name as group_name
            FROM market as m INNER JOIN  `group` as g ON m.group_id = g.id
            WHERE m.id = '%s';
        """

        for market_id in self.__market_ids(cursor):
            cursor.execute(sql % market_id)
            self.__markets.append(Market(self.__connection, self.__start_date, market_id, *cursor.fetchone()))

    def __update_studies(self):
        for market in self.__markets:
            market.update_studies()
