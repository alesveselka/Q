#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
import pandas_datareader as pdr

from sklearn.model_selection import train_test_split
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC


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
    for i in range(1, lags+1):
        tslag['Lag%s' % str(i)] = ts['Adj Close'].shift(i)

    # Create the returns DataFrame
    tsret = pd.DataFrame(index=tslag.index)
    tsret['Volume'] = tslag['Volume']
    tsret['Today'] = tslag['Today'].pct_change() * 100.0

    # If any of the values of percentage returns equal zero, set them to
    # a small number (stops issues with QDA  model in Scikit-Learn)
    for i,x in enumerate(tsret['Today']):
        if np.isnan(x) or abs(x) < 0.0001:
            tsret['Today'][i] = 0.0001

    # Create the lagged percentage returns columns
    for i in range(1, lags+1):
        col = 'Lag%s' % str(i)
        tsret[col] = tslag[col].pct_change() * 100.0
        # Reset NaN values to 0.0s
        for j, x in enumerate(tsret[col]):
            if np.isnan(x): tsret[col][j] = 0.0

    # Create the 'Direction' column (+1 or -1) indicating an up/down day
    tsret['Direction'] = np.sign(tsret['Today'])
    tsret = tsret[tsret.index >= start_date]

    return tsret


def main():
    # Create a lagged series of the S&P 500 US stock market index
    snpret = create_lagged_series('^GSPC', dt.datetime(2001, 1, 10), dt.datetime(2005, 12, 31))

    # Use the prior two days of returns as predictor
    # values, with direction as the response
    X = snpret[['Lag1', 'Lag2']]
    y = snpret['Direction']

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)

    # Set the parameters by cross-validation
    tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-3, 1e-4], 'C': [1, 10, 100, 1000]}]

    # Perform the grid search on the tuned parameters
    model = GridSearchCV(SVC(C=1), tuned_parameters, cv=10)
    model.fit(X_train, y_train)

    print "Optimized parameters found on training set:"
    print model.best_estimator_, "\n"

    print "Grid scores calculated on training set:"
    for params, mean_score, scores in model.grid_scores_:
        print "%0.3f for %r" % (mean_score, params)

if __name__ == "__main__":
    main()
