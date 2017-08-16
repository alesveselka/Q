#!/usr/bin/python

import sys
import json
from enum import Table
from currency_pair import CurrencyPair
from interest_rate import InterestRate
from market import Market
from series.norgate_series import NorgateSeries
from series.custom_series import CustomSeries


class DataSeries:

    def __init__(self, investment_universe, connection, study_parameters):

        self.__investment_universe = investment_universe
        self.__connection = connection
        self.__futures = None
        self.__currency_pairs = None
        self.__interest_rates = None
        self.__study_parameters = study_parameters

    def start_date(self):
        """
        Return data's start data date
        :return:    date
        """
        return self.__investment_universe.start_data_date()

    def futures(self, slippage_map, roll_strategy):
        """
        Load futures data if not already loaded

        :param slippage_map:        list of dicts, each representing volume range to arrive at slippage estimate
        :param roll_strategy:       contract roll strategy
        :return:                    list of Market objects
        """
        if self.__futures is None:
            cursor = self.__connection.cursor()
            market_query = """
                SELECT
                  name,
                  code,
                  data_codes,
                  currency,
                  tick_value,
                  point_value,
                  overnight_initial_margin
                FROM market 
                WHERE id = '%s';
            """
            start_data_date = self.__investment_universe.start_data_date()
            self.__futures = []

            series_class = NorgateSeries if roll_strategy[Table.RollStrategy.NAME] == 'norgate' else CustomSeries
            loaded_roll_strategy = (
                roll_strategy[Table.RollStrategy.ID],
                roll_strategy[Table.RollStrategy.NAME],
                roll_strategy[Table.RollStrategy.TYPE],
                json.loads(roll_strategy[Table.RollStrategy.PARAMS])
                if roll_strategy[Table.RollStrategy.PARAMS] else None,
            )

            for market_id in self.__investment_universe.market_ids():
            # for market_id in [33]:  # 100 = CL2, 33 = W2, 19 = SB
                cursor.execute(market_query % market_id)
                self.__futures.append(Market(
                    market_id,
                    slippage_map,
                    series_class(start_data_date, self.__study_parameters, loaded_roll_strategy),
                    *cursor.fetchone())
                )

        return self.__futures

    def currency_pairs(self, base_currency, commission_currency):
        """
        Load currency_pair data if not already loaded

        :param base_currency:       string representing base currency
        :param commission_currency: string representing commission currency
        :return:                    list of CurrencyPair objects
        """
        if self.__currency_pairs is None:
            cursor = self.__connection.cursor()
            cursor.execute("""
                SELECT c.id, c.code, c.name, c.first_data_date
                FROM currency_pairs as c INNER JOIN `group` as g ON c.group_id = g.id
                WHERE g.name = 'Primary';
            """)
            start_data_date = self.__investment_universe.start_data_date()
            futures_currencies = list(set([f.currency() for f in self.__futures] + [base_currency, commission_currency]))
            futures_currency_pairs = ['%s%s' % (base_currency, c) for c in futures_currencies if c != base_currency]
            futures_currency_data = [c for c in cursor.fetchall() if c[1] in futures_currency_pairs]
            self.__currency_pairs = [CurrencyPair(start_data_date, *c) for c in futures_currency_data]

        return self.__currency_pairs

    def interest_rates(self, base_currency, commission_currency):
        """
        Load interest_rate data if not already loaded

        :param base_currency:       string representing base currency
        :param commission_currency: string representing commission currency
        :return:                    list of InterestDate objects
        """
        if self.__interest_rates is None:
            cursor = self.__connection.cursor()
            cursor.execute("""
                SELECT c.id, c.code
                FROM `currencies` as c INNER JOIN `group` as g ON c.group_id = g.id
                WHERE g.name = 'Majors'
            """)
            start_data_date = self.__investment_universe.start_data_date()
            futures_currencies = list(set([f.currency() for f in self.__futures] + [base_currency, commission_currency]))
            futures_currency_data = [c for c in cursor.fetchall() if c[1] in futures_currencies]
            self.__interest_rates = [InterestRate(start_data_date, *r) for r in futures_currency_data]

        return self.__interest_rates

    def update_futures_data(self, date):
        """
        Update futures data and their studies
        
        :param date:    date of the data to update
        """
        map(lambda f: f.update_data(date), self.__futures)

    def update_futures_studies(self, date):
        """
        Update futures studies
        
        :param date:    date of the data to update
        """
        map(lambda f: f.update_studies(date), self.__futures)

    def load(self, end_date, roll_strategy_id):
        """
        Load data and calculate studies

        :param end_date:            last date to load data
        :param roll_strategy_id:    ID of the series roll strategy
        """
        cursor = self.__connection.cursor()
        cursor.execute("SELECT code, short_name FROM `delivery_month`;")
        delivery_months = {i[1][0]: (i[0] + 1, i[1][1]) for i in enumerate(cursor.fetchall())}

        # TODO load all at once and then filter in python?
        message = 'Loading Futures data ...'
        length = float(len(self.__futures))
        map(lambda i: self.__log(message, i[1].code(), i[0], length)
                      and i[1].load_data(self.__connection, end_date, delivery_months, roll_strategy_id), enumerate(self.__futures))
        self.__log(message, complete=True)

        # TODO load all at once and then filter in python?
        message = 'Loading currency pairs data ...'
        length = float(len(self.__currency_pairs))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(self.__currency_pairs))
        self.__log(message, complete=True)

        # TODO load all at once and then filter in python?
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
