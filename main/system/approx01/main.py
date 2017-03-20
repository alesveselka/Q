#!/usr/bin/python

import sys
import os
import MySQLdb as mysql
from timer import Timer
from risk import Risk
from investment_universe import InvestmentUniverse
from trading_system import TradingSystem


def main(universe_name):
    timer = Timer(0.0)
    connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )
    risk_position_sizing = 0.002
    system = TradingSystem(
        InvestmentUniverse(universe_name, timer, connection),
        Risk(risk_position_sizing)
    )
    timer.start()  # TODO start after data is loaded

if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        main(sys.argv[1])
    else:
        print 'Expected one argument - name of the investment universe'