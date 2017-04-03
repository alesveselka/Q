#!/usr/bin/python

import datetime
from enum import EventType
from market import Market
from currency_pair import CurrencyPair
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
        self.__currency_pairs = []  # TODO separate currency pairs and make it available to broker as well

        # TODO trigger the start and loading on 'subscription' from other objects?
        self.__timer.on(EventType.HEARTBEAT, self.__on_timer_heartbeat)

    def __on_timer_heartbeat(self, *data):
        self.__load_markets()  # TODO load only when study is updated?
        self.__update_studies()

        self.dispatch(EventType.MARKET_DATA, self.__markets, self.__start_data_date)

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
        market_query = """
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
        # for market_id in data[2].split(','):
        for market_id in [int(data[2].split(',')[16])]:  # JY = 37@25Y, W = 16@25Y, ES = 74@15Y
            cursor.execute(market_query % market_id)
            self.__markets.append(Market(
                self.__connection,
                self.__start_contract_date,
                self.__start_data_date,
                market_id,
                *cursor.fetchone()
            ))

        currency_query = """
            SELECT
                c.id,
                c.code,
                c.name,
                c.first_data_date
            FROM currency_pairs as c INNER JOIN `group` as g ON c.group_id = g.id
            WHERE g.name = 'Primary';
        """

        cursor.execute(currency_query)
        result = cursor.fetchall()
        for c in result:
            self.__currency_pairs.append(CurrencyPair(
                self.__connection,
                self.__start_data_date,
                *c
            ))

    def __update_studies(self):
        for market in self.__markets:
            market.update_studies()

        for currency_pair in self.__currency_pairs:
            currency_pair.load_data()

    def currency_pairs(self):
        return self.__currency_pairs

    def currency_pair(self, pair):
        return [cp for cp in self.__currency_pairs if cp.code() == pair]
