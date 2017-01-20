#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
import sklearn
import pandas_datareader as pdr

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
from sklearn.metrics import confusion_matrix
from sklearn.svm import LinearSVC, SVC

def create_lagged_series(symbol, start_date, end_date, lags=5):
    """
    Creates a pandas DataFrame that stores the percentage returns
    of adjusted closing value of a stock obtained from Yahoo Finance,
    along with a number of lagged returns from the prior trading days
    (lags default to 5). Trading volume, as well as the Direction 
    from the previous day, are also included.
    """
    # Obtain stock information from Yahoo Finance
    ts = pdr.get_data_yahoo(symbol, start_date, end_date)

    # Create the new lagged DataFrame
    tslag = pd.DataFrame(index=ts.index)
    tslag['Today'] = ts['Adj Close']
    tslag['Volume'] = ts['Volume']

    # Create the shifted lag series of prior trading period close values
    for i in range(0, lags):
        tslag['Lag%s' % str(i+1)] = ts['Adj Close'].shift(i+1)

    # Create the returns DataFrame
    tsret = pd.DataFrame(index=tslag.index)
    tsret['Volume'] = tslag['Volume']
    tsret['Today'] = tslag['Today'].pct_change() * 100.0

    # If any of the values of percentage returns equal zero, set them to
    # a small number (stops issues with QDA  model in Scikit-Learn)
    for i,x in enumerate(tsret['Today']):
        if (abs(x) < 0.0001):
            tsret['Today'] = 0.0001

    # Create the lagged percentage returns columns
    for i in range(0, lags):
        tsret['Lag%s' % str(i+1)] = tslag['Lag%s' % str(i+1)].pct_change() * 100.0

    # Create the 'Direction' column (+1 or -1) indicating an up/down day
    tsret['Direction'] = np.sign(tsret['Today'])
    tsret = tsret[tsret.index >= start_date]

    return tsret

def main():
    print create_lagged_series('AMZN', dt.datetime(2012, 1, 1), dt.datetime(2013, 1, 1))

if __name__ == "__main__":
    main()
