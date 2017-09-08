#!/usr/bin/python

import sys
from operations.initialize import Initialize

if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        Initialize(sys.argv[1])
    else:
        print 'Expected one argument - name of the simulation'
