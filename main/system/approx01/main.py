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
from interest_rate import InterestRate
from trading_system import TradingSystem
from decimal import Decimal


def interest_rates():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT c.id, c.code
        FROM `currencies` as c INNER JOIN `group` as g ON c.group_id = g.id
        WHERE g.name = 'Majors'
    """)
    return [InterestRate(*r) for r in cursor.fetchall()]


def main(universe_name):
    timer = Timer(0.0)
    risk_position_sizing = Decimal(0.002)
    commission = 10.0  # TODO convert to base-currency
    # TODO load currency-pairs here first and then start the rest
    rates = interest_rates()
    investment_universe = InvestmentUniverse(universe_name, timer, connection)
    account = Account(Decimal(1e6), Currency.EUR, investment_universe)
    portfolio = Portfolio()
    system = TradingSystem(
        investment_universe,
        Risk(risk_position_sizing),
        account,  # TODO access from broker?
        portfolio,  # TODO access from broker?
        Broker(account, portfolio, commission, investment_universe)
    )
    map(lambda r: r.load_data(connection), rates)
    # timer.start()  # TODO start after data is loaded

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
