#!/usr/bin/python

import os
import MySQLdb as mysql
from timer import Timer
from risk import Risk
from portfolio import Portfolio
from account import Account
from broker import Broker
from enum import Currency
from enum import Study
from enum import Table
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
        timer = Timer()
        risk_position_sizing = Decimal(0.002)
        commission = 10.0  # TODO convert to base-currency
        params = self.__study_parameters()

        investment_universe = InvestmentUniverse(investment_universe_name, connection)
        investment_universe.load_data()

        data_series = DataSeries(investment_universe, connection)
        futures = data_series.futures()
        currency_pairs = data_series.currency_pairs()
        interest_rates = data_series.interest_rates()
        account = Account(Decimal(1e6), Currency.EUR, currency_pairs)
        portfolio = Portfolio()
        broker = Broker(timer, account, portfolio, commission, currency_pairs, interest_rates)
        system = TradingSystem(
            timer,
            futures,
            Risk(risk_position_sizing),
            account,  # TODO access from broker?
            portfolio,  # TODO access from broker?
            broker
        )

        map(lambda f: f.load_data(connection) and f.calculate_studies(params), futures)
        map(lambda cp: cp.load_data(connection), currency_pairs)
        map(lambda r: r.load_data(connection), interest_rates)

        system.subscribe()
        broker.subscribe()
        timer.start(investment_universe.start_data_date())

    def __study_parameters(self):
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
