#!/usr/bin/python

import sys
import datetime
from timer import Timer
from investment_universe import InvestmentUniverse
from trading_system import TradingSystem


def main(universe_name):
    timer = Timer(0.0)
    start_date = datetime.date(1992, 03, 01)
    system = TradingSystem(InvestmentUniverse(universe_name, start_date, timer))
    timer.start()  # TODO start after data is loaded

if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        main(sys.argv[1])
    else:
        print 'Expected one argument - name of the investment universe'
