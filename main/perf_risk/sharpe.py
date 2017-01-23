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

def market_neutral_sharpe(ticker, benchmark):
    """
    Calculates the annualised Sharpe ratio of a market neutral
    long/short strategy involving the long of 'ticker'
    with a corresponding short of the 'benchmark'.
    """
    start = dt.datetime(2000, 1, 1)
    end = dt.datetime(2013, 1, 1)

    # Get historical data for both a symbol/ticker and a benchmark ticker
    # The dates have been hard-coded, but you can modify them as you see fit.
    tick = pdr.get_data_google(ticker, start, end)
    bench = pdr.get_data_google(benchmark, start, end)

    # Calculate the percentage returns on each of the time series
    tick['daily_return'] = tick['Close'].pct_change()
    bench['daily_return'] = bench['Close'].pct_change()

    # Create a new DataFrame to store the strategy information
    # The net returns are (long - short) / 2, since there is twice
    # the trading capital for this strategy
    strategy = pd.DataFrame(index=tick.index)
    strategy['net_return'] = (tick['daily_return'] - bench['daily_return']) / 2

    # Return annualized Sharpe ratio for this strategy
    return annualised_sharpe(strategy['net_return'])

if __name__ == "__main__":
    print equity_sharpe('GOOG')
    print market_neutral_sharpe('GOOG', 'SPY')
