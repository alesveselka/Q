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
from study import ATR, SMA, HHLL
from investment_universe import InvestmentUniverse
from trading_system import TradingSystem
from data_series import DataSeries
from decimal import Decimal


class Initialize:

    def __init__(self, investment_universe_name):
        connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        risk_position_sizing = Decimal(0.002)
        commission = (10.0, Currency.USD)

        now = dt.datetime.now()
        # end_date = dt.date(now.year, now.month, now.day)
        end_date = dt.date(1992, 6, 10)
        # end_date = dt.date(2015, 12, 31)
        timer = Timer()

        investment_universe = InvestmentUniverse(investment_universe_name, connection)
        investment_universe.load_data()
        self.__start_date = investment_universe.start_data_date()

        data_series = DataSeries(investment_universe, connection)
        futures = data_series.futures()
        currency_pairs = data_series.currency_pairs()
        interest_rates = data_series.interest_rates()

        self.__account = Account(Decimal(1e6), Currency.EUR, currency_pairs)

        portfolio = Portfolio()
        risk = Risk(risk_position_sizing, self.__account)

        self.__broker = Broker(timer, self.__account, portfolio, commission, currency_pairs, interest_rates)
        self.__trading_system = TradingSystem(timer, futures, risk, portfolio, self.__broker)

        self.__load_and_calculate_data(connection, end_date, futures, currency_pairs, interest_rates)
        self.__start(timer, self.__trading_system, end_date)

    def __start(self, timer, trading_system, end_date):
        """
        Start the system

        :param trading_system:  TradingSystem instance
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
        # TODO move printing to Reports object
        # TODO also print transaction same as in Broker!
        date = self.__start_date
        separator = ''.join([('-' * 50), ' %s ', ('-' * 50)])
        orders = self.__broker.orders()
        order = None
        print separator % 'transactions'
        for t in self.__account.transactions():
            if t.date() != date:
                print 'Equity:', float(self.__account.equity(date)), 'Funds:', float(self.__account.available_funds(date)), \
                    'Balances:', self.__account.to_fx_balance_string(date), 'Margins:', self.__account.to_margin_loans_string(date)
                date = t.date()
                print separator % date
                order = [o for o in orders if o.date() == date]
                if len(order):
                    print order[0]
            print t
        print 'Equity:', float(self.__account.equity(date)), 'Funds:', float(self.__account.available_funds(date)), \
            'Balances:', self.__account.to_fx_balance_string(date), 'Margins:', self.__account.to_margin_loans_string(date)

        print separator % 'trades'
        total = 0
        for t in self.__trading_system.trades():
            total += t.result()
            print t

        print 'Total: ', total

    def __load_and_calculate_data(self, connection, end_date, futures, currency_pairs, interest_rates):
        """
        Load data and calculate studies

        :param connection:      MySQLdb connection instance
        :param futures:         List of futures Market objects
        :param currency_pairs:  List of CurrencyPair instances
        :param interest_rates:  List of InterestRate instances
        """
        message = 'Loading Futures data ...'
        length = float(len(futures))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(connection, end_date),
            enumerate(futures))
        self.__log(message, complete=True)

        message = 'Calculating Futures studies ...'
        params = self.__study_parameters()
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].calculate_studies(params),
            enumerate(futures))
        self.__log(message, complete=True)

        message = 'Loading currency pairs data ...'
        length = float(len(currency_pairs))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(connection, end_date),
            enumerate(currency_pairs))
        self.__log(message, complete=True)

        message = 'Loading interest rates data ...'
        length = float(len(interest_rates))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(connection, end_date),
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
                Table.Futures.PRICE_DATE,
                Table.Futures.HIGH_PRICE,
                Table.Futures.LOW_PRICE,
                Table.Futures.SETTLE_PRICE
            ]},
            {'name': Study.ATR_SHORT, 'study': ATR, 'window': short_window, 'columns': [
                Table.Futures.PRICE_DATE,
                Table.Futures.HIGH_PRICE,
                Table.Futures.LOW_PRICE,
                Table.Futures.SETTLE_PRICE
            ]},
            {'name': Study.VOL_SHORT, 'study': SMA, 'window': short_window, 'columns': [
                Table.Futures.PRICE_DATE,
                Table.Futures.VOLUME
            ]},
            {'name': Study.SMA_LONG, 'study': SMA, 'window': long_window, 'columns': [
                Table.Futures.PRICE_DATE,
                Table.Futures.SETTLE_PRICE
            ]},
            {'name': Study.SMA_SHORT, 'study': SMA, 'window': short_window, 'columns': [
                Table.Futures.PRICE_DATE,
                Table.Futures.SETTLE_PRICE
            ]},
            {'name': Study.HHLL_LONG, 'study': HHLL, 'window': long_window, 'columns': [
                Table.Futures.PRICE_DATE,
                Table.Futures.SETTLE_PRICE
            ]},
            {'name': Study.HHLL_SHORT, 'study': HHLL, 'window': short_window, 'columns': [
                Table.Futures.PRICE_DATE,
                Table.Futures.SETTLE_PRICE
            ]}
        ]

    def __log(self, message, code='', index=0, length=0.0, complete=False):
        """
        Print message and percentage progress to console

        :param message:     Message to print
        :param percent:     Percentage progress to print
        :param new_line:    Flag indicating if new line should be printed as well
        :return:            boolean
        """
        sys.stdout.write('%s\r' % (' ' * 80))
        if complete:
            sys.stdout.write('%s complete\r\n' % message)
        else:
            sys.stdout.write('%s %s (%d of %d) [%d %%]\r' % (message, code, index, length, index / length * 100))
        sys.stdout.flush()
        return True
