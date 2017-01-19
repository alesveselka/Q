#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import pandas_datareader as pdr
import pprint
import statsmodels.tsa.stattools as ts
from pandas.stats.api import ols # Ordinary least squares

def plot_price_series(df, ts1, ts2):
    """
    Takes pandas DateFrame as input, with two columns given by the placeholder ts1 and ts2.
    These will be our pair equities. The function simply plot the two price series on 
    the same chart. This allow us to visually inspect whether any cointegration may be likely.
    """
    months = mdates.MonthLocator() # every month
    fig, ax = plt.subplots()
    ax.plot(df.index, df[ts1], label=ts1)
    ax.plot(df.index, df[ts2], label=ts2)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlim(dt.datetime(2012, 1, 1), dt.datetime(2013, 1, 1))
    ax.grid(True)
    fig.autofmt_xdate()

    plt.xlabel('Month/Year')
    plt.ylabel('Pricce ($)')
    plt.title('%s and %s Daily Prices' % (ts1, ts2))
    plt.legend()
    plt.show()

def plot_scatter_series(df, ts1, ts2):
    """
    Plots a scatter plot of the two prices. This allow us to visually introspect 
    whether a linear relationship exists between the two series and thus whether 
    it is a good candidate for the OLS procedure and subsequent ADF test.
    """
    plt.xlabel('%s Price ($)' % ts1)
    plt.ylabel('%s Price ($)' % ts1)
    plt.title('%s and %s Price Scatterplot' % (ts1, ts2))
    plt.scatter(df[ts1], df[ts2])
    plt.show()

def plot_residuals(df):
    """
    Plots residual values from the fitted linear model of the two price series.
    """
    months = mdates.MonthLocator() # every month
    fig, ax = plt.subplots()
    ax.plot(df.index, df['res'], label='Residuals')
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlim(dt.datetime(2012, 1, 1), dt.datetime(2013, 1, 1))
    ax.grid(True)
    fig.autofmt_xdate()

    plt.xlabel('Month/Year')
    plt.ylabel('Pricce ($)')
    plt.title('Residual Plot')
    plt.legend()

    plt.plot(df['res'])
    plt.show()

def main():
    AREX = 'AREX'
    WLL = 'WLL'
    start = dt.datetime(2012, 1, 1)
    end = dt.datetime(2013, 1, 1)

    arex = pdr.get_data_yahoo(AREX, start, end)
    wll = pdr.get_data_yahoo(WLL, start, end)

    df = pd.DataFrame(index=arex.index)
    df[AREX] = arex['Adj Close']
    df[WLL] = wll['Adj Close']

    # Plot the two price series
    plot_price_series(df, AREX, WLL)

    # Display a scatter plot of the two time series
    plot_scatter_series(df, AREX, WLL)

    # Calculate optimal hedge ratio "beta"
    res = ols(y=df[WLL], x=df[AREX])
    beta_hedge_ratio = res.beta.x

    # Calculate the residuals of the linear combination
    df['res'] = df[WLL] - beta_hedge_ratio * df[AREX]

    # Plot the residuals
    plot_residuals(df)

    # Calculate and output  the CADF test on the residuals
    cadf = ts.adfuller(df['res'])
    pprint.pprint(cadf)

if __name__ == "__main__":
    main()
