#!/usr/bin/python

import datetime
from enum import EventType
from market import Market
from event_dispatcher import EventDispatcher


class InvestmentUniverse(EventDispatcher):

    def __init__(self, name, timer, connection):
        super(InvestmentUniverse, self).__init__()

        self.__name = name
        self.__start_contract_date = None
        self.__start_data_date = None
        self.__timer = timer
        self.__connection = connection
        self.__markets = []

        # TODO trigger the start and loading on 'subscription' from other objects?
        self.__timer.on(EventType.HEARTBEAT, self.__on_timer_heartbeat)

    def __on_timer_heartbeat(self, *data):
        self.__load_markets()  # TODO load only when study is updated?
        self.__update_studies()

        # Simulate available data as they come in ...
        # now = datetime.datetime.now()
        # today = datetime.date(now.year, now.month, now.day)
        # delta = today - self.__start_data_date  # TODO replace 'today' with last available data
        # print delta

        # for date in (self.__start_data_date + datetime.timedelta(n) for n in range(delta.days)):
        #     # print self.__start_data_date, date, len([m for m in self.__markets if len(m.data(self.__start_data_date, date))])
        #     self.dispatch(EventType.MARKET_DATA, {
        #         'start_date': self.__start_data_date,
        #         'end_date': date,
        #         'markets': self.__markets
        #     })

        # self.dispatch(EventType.MARKET_DATA, self.__markets, self.__start_data_date)

    def __load_data(self, cursor):
        # TODO 'query' object?
        cursor.execute("""
            SELECT contract_start_date, data_start_date, market_ids
            FROM investment_universe
            WHERE name = '%s';
        """ % self.__name)
        return cursor.fetchone()

    def __load_markets(self):
        # TODO 'query' object?
        cursor = self.__connection.cursor()
        # TODO replace with 'entity'?
        sql = """
            SELECT
              m.name,
              m.code,
              m.data_codes,
              m.currency,
              m.first_data_date,
              g.name as group_name,
              m.tick_value,
              m.point_value,
              m.overnight_initial_margin
            FROM market as m INNER JOIN  `group` as g ON m.group_id = g.id
            WHERE m.id = '%s';
        """
        data = self.__load_data(cursor)
        self.__start_contract_date = data[0]  # TODO remove hard-coded index
        self.__start_data_date = data[1]  # TODO remove hard-coded index
        # print data[2].split(',').index('33')
        for market_id in data[2].split(','):
        # for market_id in [int(data[2].split(',')[74])]:  # JY = 37@25Y, W = 16@25Y, ES = 74@15Y
            cursor.execute(sql % market_id)
            self.__markets.append(Market(
                self.__connection,
                self.__start_contract_date,
                self.__start_data_date,
                market_id,
                *cursor.fetchone())
            )

        # TODO query single markets here, join calculated studies and dispatch event with fetched data for System; iterate for each symbol

    def __update_studies(self):
        for market in self.__markets:
            market.update_studies()
