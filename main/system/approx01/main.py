#!/usr/bin/python

import sys
from universe import Universe


def main(universe_name):
    universe = Universe(universe_name)
    universe.markets()

if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        main(sys.argv[1])
    else:
        print 'Expected one argument - name of the investment universe'
