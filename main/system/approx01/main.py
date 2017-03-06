#!/usr/bin/python

import sys
from investment_universe import InvestmentUniverse


def main(universe_name):
    universe = InvestmentUniverse(universe_name)
    for m in universe.markets():
        print m

if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        main(sys.argv[1])
    else:
        print 'Expected one argument - name of the investment universe'
