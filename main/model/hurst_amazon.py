#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import pandas_datareader as pdr
from numpy import cumsum, log, polyfit, sqrt, std, subtract
from numpy.random import randn

def hurst(ts):
    """
    Returns the Hurst Exponent of the time series vector 'ts' 
    """
    # Create the range of lag values
    lags = range(2, 100)

    # Calculate the array fo the variances of the lagged differences
    tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]

    # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)

    # Return the Hurst Exponent from the polyfit output
    return poly[0] * 2.0

if __name__ == "__main__":
    # Create a Geometric Brownian Motion, Mean-Reverting and trending series
    gbm = log(cumsum(randn(100000))+1000)
    mr = log(randn(100000)+1000)
    tr = log(cumsum(randn(100000)+1)+1000)
    amzn = pdr.get_data_yahoo("AMZN", dt.datetime(2000, 1, 1), dt.datetime(2015, 1, 1))

    # Output the Hurst Exponent for each of the above series
    # and the price of Amazon (the Adjusted Close) for the ADF test
    # given above in the article
    print "Hurst(GBM):   %s" % hurst(gbm)
    print "Hurst(MR):    %s" % hurst(mr)
    print "Hurst(TR):    %s" % hurst(tr)
    print "Hurst(AMZN):  %s" % hurst(amzn['Adj Close'])
