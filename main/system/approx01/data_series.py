#!/usr/bin/python

from market import Market
from currency_pair import CurrencyPair
from interest_rate import InterestRate
from event_dispatcher import EventDispatcher


class DataSeries(EventDispatcher):

    def __init__(self, investment_universe, connection):
        super(DataSeries, self).__init__()

        self.__investment_universe = investment_universe
        self.__connection = connection
        self.__futures = None
        self.__currency_pairs = None
        self.__interest_rates = None

    def futures(self):
        """
        Load futures data if not already loaded

        :return:    list of Market objects
        """
        if self.__futures is None:
            cursor = self.__connection.cursor()
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
            start_data_date = self.__investment_universe.start_data_date()
            self.__futures = []
            # for market_id in [int(self.__investment_universe.market_ids()[37])]:  # JY = 37@25Y, W = 16@25Y, ES = 74@15Y
            for market_id in self.__investment_universe.market_ids():
                cursor.execute(market_query % market_id)
                self.__futures.append(Market(start_data_date, market_id, *cursor.fetchone()))

        return self.__futures

    def currency_pairs(self):
        """
        Load currency_pair data if not already loaded

        :return:    list of CurrencyPair objects
        """
        if self.__currency_pairs is None:
            cursor = self.__connection.cursor()
            cursor.execute("""
                SELECT c.id, c.code, c.name, c.first_data_date
                FROM currency_pairs as c INNER JOIN `group` as g ON c.group_id = g.id
                WHERE g.name = 'Primary';
            """)
            start_data_date = self.__investment_universe.start_data_date()
            self.__currency_pairs = [CurrencyPair(start_data_date, *c) for c in cursor.fetchall()]

        return self.__currency_pairs

    def interest_rates(self):
        """
        Load interest_rate data if not already loaded

        :return: list of InterestDate objects
        """
        if self.__interest_rates is None:
            cursor = self.__connection.cursor()
            cursor.execute("""
                SELECT c.id, c.code
                FROM `currencies` as c INNER JOIN `group` as g ON c.group_id = g.id
                WHERE g.name = 'Majors'
            """)
            start_data_date = self.__investment_universe.start_data_date()
            self.__interest_rates = [InterestRate(start_data_date, *r) for r in cursor.fetchall()]

        return self.__interest_rates
