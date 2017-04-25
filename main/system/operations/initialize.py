#!/usr/bin/python

import os
import sys
import MySQLdb as mysql
import datetime as dt
from timer import Timer
from risk import Risk
from portfolio import Portfolio
from account import Account
from broker import Broker
from enum import Currency
from enum import Study
from enum import Table
from enum import EventType
from enum import Interval
from study import ATR, SMA, HHLL
from investment_universe import InvestmentUniverse
from trading_system import TradingSystem
from data_series import DataSeries
from persist import Persist
from report import Report
from decimal import Decimal


class Initialize:

    def __init__(self, investment_universe_name):
        # TODO set Decimal context?

        self.__connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        # TODO load from external config
        risk_position_sizing = Decimal(0.002)
        commission = (10.0, Currency.USD)
        minimums = {'AUD': 14000, 'CAD': 14000, 'CHF': 100000, 'EUR': 100000, 'GBP': 8000, 'JPY': 11000000, 'USD': 10000}

        now = dt.datetime.now()
        # end_date = dt.date(now.year, now.month, now.day)
        end_date = dt.date(1992, 6, 10)
        # end_date = dt.date(2015, 12, 31)
        timer = Timer()

        investment_universe = InvestmentUniverse(investment_universe_name, self.__connection)
        investment_universe.load_data()
        self.__start_date = investment_universe.start_data_date()

        data_series = DataSeries(investment_universe, self.__connection)
        self.__futures = data_series.futures()
        currency_pairs = data_series.currency_pairs()
        interest_rates = data_series.interest_rates()

        self.__account = Account(Decimal(1e6), Currency.EUR, currency_pairs)
        self.__portfolio = Portfolio()

        risk = Risk(risk_position_sizing, self.__account)

        self.__broker = Broker(timer, self.__account, self.__portfolio, commission, currency_pairs, interest_rates, minimums)
        self.__trading_system = TradingSystem(timer, self.__futures, risk, self.__portfolio, self.__broker)

        self.__load_and_calculate_data(self.__futures, currency_pairs, interest_rates, end_date)
        self.__start(timer, self.__trading_system, end_date)
        # self.__on_timer_complete(end_date)

    def __start(self, timer, trading_system, end_date):
        """
        Start the system

        :param timer:           Timer instance
        :param trading_system:  TradingSystem instance
        :param end_date:        date of end of simulation
        """
        trading_system.subscribe()
        self.__broker.subscribe()
        timer.on(EventType.COMPLETE, self.__on_timer_complete)
        timer.start(self.__start_date, end_date)

    def __on_timer_complete(self, date):
        """
        Timer Complete event handler

        :param date:    date of the complete event
        """
        Persist(
            self.__connection,
            self.__start_date,
            date,
            self.__broker.order_results(),
            self.__account,
            self.__portfolio,
            self.__futures,
            self.__study_parameters()
        )

        report = Report(self.__account)
        # print '\n'.join(report.transactions(self.__start_date, date))
        print '\n'.join(report.to_lists(self.__start_date, date, Interval.YEARLY))
        print '\n'.join(report.to_lists(self.__start_date, date))

    def __load_and_calculate_data(self, futures, currency_pairs, interest_rates, end_date):
        """
        Load data and calculate studies

        :param futures:         List of futures Market objects
        :param currency_pairs:  List of CurrencyPair instances
        :param interest_rates:  List of InterestRate instances
        :param end_date:        last date to load data
        """
        message = 'Loading Futures data ...'
        length = float(len(futures))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(futures))
        self.__log(message, complete=True)

        message = 'Calculating Futures studies ...'
        params = self.__study_parameters()
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].calculate_studies(params),
            enumerate(futures))
        self.__log(message, complete=True)

        message = 'Loading currency pairs data ...'
        length = float(len(currency_pairs))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(currency_pairs))
        self.__log(message, complete=True)

        message = 'Loading interest rates data ...'
        length = float(len(interest_rates))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(interest_rates))
        self.__log(message, complete=True)

    def __study_parameters(self):
        """
        :return:    List of dictionaries with parameters for study calculations
        """
        short_window = 50
        long_window = 100
        return [
            {'name': Study.ATR_LONG, 'study': ATR, 'window': long_window, 'columns': [
                Table.Market.PRICE_DATE,
                Table.Market.HIGH_PRICE,
                Table.Market.LOW_PRICE,
                Table.Market.SETTLE_PRICE
            ]},
            {'name': Study.ATR_SHORT, 'study': ATR, 'window': short_window, 'columns': [
                Table.Market.PRICE_DATE,
                Table.Market.HIGH_PRICE,
                Table.Market.LOW_PRICE,
                Table.Market.SETTLE_PRICE
            ]},
            {'name': Study.VOL_SHORT, 'study': SMA, 'window': short_window, 'columns': [
                Table.Market.PRICE_DATE,
                Table.Market.VOLUME
            ]},
            {'name': Study.SMA_LONG, 'study': SMA, 'window': long_window, 'columns': [
                Table.Market.PRICE_DATE,
                Table.Market.SETTLE_PRICE
            ]},
            {'name': Study.SMA_SHORT, 'study': SMA, 'window': short_window, 'columns': [
                Table.Market.PRICE_DATE,
                Table.Market.SETTLE_PRICE
            ]},
            {'name': Study.HHLL_LONG, 'study': HHLL, 'window': long_window, 'columns': [
                Table.Market.PRICE_DATE,
                Table.Market.SETTLE_PRICE
            ]},
            {'name': Study.HHLL_SHORT, 'study': HHLL, 'window': short_window, 'columns': [
                Table.Market.PRICE_DATE,
                Table.Market.SETTLE_PRICE
            ]}
        ]

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
