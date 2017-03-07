#!/usr/bin/python

import sys
import datetime
import os
import MySQLdb as mysql
from timer import Timer
from investment_universe import InvestmentUniverse
from trading_system import TradingSystem


def main(universe_name):
    timer = Timer(0.0)
    start_date = datetime.date(1992, 03, 01)  # TODO possibly more than exactly 25 years ...
    connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )
    system = TradingSystem(InvestmentUniverse(universe_name, start_date, timer, connection))
    timer.start()  # TODO start after data is loaded

if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        main(sys.argv[1])
    else:
        print 'Expected one argument - name of the investment universe'
