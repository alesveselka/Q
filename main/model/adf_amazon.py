#!/usr/bin/python
# -*- coding: utf-8 -*-

# Import the Time Series library
import statsmodels.tsa.stattools as ts

# Import Datetime and Pandas DataReader
import datetime as dt
import pandas_datareader as pdr

# Download the Amazon OHLCV data from 1/1/2000 to 1/1/2015
amzn = pdr.get_data_yahoo("AMZN", dt.datetime(2000, 1, 1), dt.datetime(2015, 1, 1))

# Output the results of the Augmented Dickey-Fuller test for Amazon
# with a lag order value of 1
print ts.adfuller(amzn['Adj Close'], 1)
