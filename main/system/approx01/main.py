#!/usr/bin/python

import sys
import os
import MySQLdb as mysql
from timer import Timer
from risk import Risk
from portfolio import Portfolio
from account import Account
from broker import Broker
from enum import Currency
from investment_universe import InvestmentUniverse
from trading_system import TradingSystem
from data_series import DataSeries
from decimal import Decimal


def main(universe_name):
    timer = Timer(0.0)
    risk_position_sizing = Decimal(0.002)
    commission = 10.0  # TODO convert to base-currency

    investment_universe = InvestmentUniverse(universe_name, connection)
    investment_universe.load_data()

    data_series = DataSeries(investment_universe, connection)
    currency_pairs = data_series.currency_pairs()
    interest_rates = data_series.interest_rates()
    account = Account(Decimal(1e6), Currency.EUR, currency_pairs)
    portfolio = Portfolio()
    system = TradingSystem(
        investment_universe,
        Risk(risk_position_sizing),
        account,  # TODO access from broker?
        portfolio,  # TODO access from broker?
        Broker(account, portfolio, commission, currency_pairs, interest_rates)
    )
    map(lambda cp: cp.load_data(connection), currency_pairs)
    map(lambda r: r.load_data(connection), interest_rates)
    timer.start()  # TODO start after data is loaded

if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        main(sys.argv[1])
    else:
        print 'Expected one argument - name of the investment universe'
