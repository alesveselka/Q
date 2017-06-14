#!/usr/bin/python

import sys
import json
from market import Market
from enum import Table
from currency_pair import CurrencyPair
from interest_rate import InterestRate


class DataSeries:

    def __init__(self, investment_universe, connection, studies):

        self.__investment_universe = investment_universe
        self.__connection = connection
        self.__studies = studies
        self.__futures = None
        self.__currency_pairs = None
        self.__interest_rates = None
        self.__study_parameters = []

    def start_date(self):
        """
        Return data's start data date
        :return:    date
        """
        return self.__investment_universe.start_data_date()

    def futures(self, roll_strategy_id, slippage_map):
        """
        Load futures data if not already loaded

        :param roll_strategy_id:    ID of the roll strategy used to connect contract data
        :param slippage_map:        list of dicts, each representing volume range to arrive at slippage estimate
        :return:                    list of Market objects
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

            for market_id in self.__investment_universe.market_ids():
                cursor.execute(market_query % market_id)
                self.__futures.append(Market(
                    start_data_date,
                    market_id,
                    roll_strategy_id,
                    slippage_map,
                    *cursor.fetchone())
                )

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

    def load_and_calculate_data(self, end_date):
        """
        Load data and calculate studies

        :param end_date:        last date to load data
        """
        cursor = self.__connection.cursor()
        cursor.execute("SELECT code, short_name FROM `delivery_month`;")
        delivery_months = cursor.fetchall()

        message = 'Loading Futures data ...'
        length = float(len(self.__futures))
        map(lambda i: self.__log(message, i[1].code(), i[0], length)
                      and i[1].load_data(self.__connection, end_date, delivery_months), enumerate(self.__futures))
        self.__log(message, complete=True)

        message = 'Calculating Futures studies ...'
        self.__study_parameters = json.loads(self.__studies)
        for s in self.__study_parameters:
            s['study'] = getattr(sys.modules['study'], s['study'])
            s['columns'] = [Table.Market.__dict__[c.upper()] for c in s['columns']]

        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].calculate_studies(self.__study_parameters),
            enumerate(self.__futures))
        self.__log(message, complete=True)

        message = 'Loading currency pairs data ...'
        length = float(len(self.__currency_pairs))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(self.__currency_pairs))
        self.__log(message, complete=True)

        message = 'Loading interest rates data ...'
        length = float(len(self.__interest_rates))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(self.__interest_rates))
        self.__log(message, complete=True)

    def study_parameters(self):
        """
        Return Studies' parameters
        :return: 
        """
        return self.__study_parameters

    def __log(self, message, code='', index=0, length=0.0, complete=False):
        """
        Print message and percentage progress to console

        :param message:     Message to print
        :param index:       Index of the item being processed
        :param length:      Length of the whole range
        :param complete:    Flag indicating if the progress is complete
        :return:            boolean
        """
        sys.stdout.write('%s\r' % (' ' * 80))
        if complete:
            sys.stdout.write('%s complete\r\n' % message)
        else:
            sys.stdout.write('%s %s (%d of %d) [%d %%]\r' % (message, code, index, length, index / length * 100))
        sys.stdout.flush()
        return True
