#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
import pandas_datareader as pdr

def annualised_sharpe(returns, N=252):
    """
    Calculate the annualised Sharpe ratio of a returns stream
    based on a number of trading periods, N. N defaults to 252,
    which then assumes a stream of daily returns.

    The funcion assumes that the returns are the excess of those
    compared to a benchmark.
    """
    return np.sqrt(N) * returns.mean() / returns.std()

def equity_sharpe(ticker):
    """
    Calculates the annualised Sharpe ratio based on the daily returns
    of an equity ticker symbol listed in Google Finance.

    The dates have been hard-coded here for brevity.
    """
    start = dt.datetime(2000, 1, 1)
    end = dt.datetime(2013, 1, 1)

    # Obtain the equities daily historic data for the desired time period
    # and add to a pandas DataFrame
    pdf = pdr.get_data_google(ticker, start, end)

    # Use the percentage change method to easily calculate daily returns
    pdf['daily_return'] = pdf['Close'].pct_change()

    # Assume an average annual risk-free rate over the period of 5 %
    pdf['excess_daily_return'] = pdf['daily_return'] - 0.05/252

    # Return the annualised Sharpe ratio based on the excess daily returns
    return annualised_sharpe(pdf['excess_daily_return'])

if __name__ == "__main__":
    print equity_sharpe('GOOG')
