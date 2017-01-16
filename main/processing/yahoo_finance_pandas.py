#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import pandas_datareader as pdr

if __name__ == "__main__":
    spy = pdr.get_data_yahoo(
        "SPY",
        datetime.datetime(2007, 1, 1),
        datetime.datetime(2015, 6, 15)
    )
    print spy.tail()
