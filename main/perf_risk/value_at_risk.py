#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas_datareader as pdr
from scipy.stats import norm

def var_cov_var(P, c, mu, sigma):
    """
    Variance-Covariance calculation of daily Value-at-Risk
    using confidence level 'c', with mean of returns 'mu'
    and standard deviation of returns 'sigma', on a portfolio 
    of value 'P'.
    """
    alpha = norm.ppf(1-c, mu, sigma)
    return P - P * (alpha + 1)

if __name__ == "__main__":
    start = dt.datetime(2010, 1, 1)
    end = dt.datetime(2014, 1, 1)

    citi = pdr.get_data_yahoo('C', start, end)
    citi['returns'] = citi['Adj Close'].pct_change()

    P = 1e6     # 1,000,000 USD
    c = 0.99    # 99 % confidence interval
    mu = np.mean(citi['returns'])
    sigma = np.std(citi['returns'])
    var = var_cov_var(P, c, mu, sigma)

    print 'Value-at-Risk: $%0.2f' % var
