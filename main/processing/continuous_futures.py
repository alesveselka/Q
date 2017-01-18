#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import numpy as np
import pandas as pd
import quandl
import os

def futures_rollover_weights(start_date, expiry_dates, contracts, rollover_days=5):
    """
    This constructs a pandas DataFrame that contains weights (between 0.0 and 1.0) 
    of contract positions to hold in order to carry out a rollover of rollover_days 
    prior to the expiration of the earliest contract. The matric can then by 'multiplied' 
    with another DataFrame containing  the settle prices of each contract in order 
    to produce a continuous time series futures contract.
    """
    # Construct a sequence of dates beginning from the earliest contract start date
    # to the end date of the final contract
    dates = pd.date_range(start_date, expiry_dates[-1], freq='B')

    # Create the 'roll weights' DataFrame that will store the multipliers 
    # for each contract (between 0.0 and 1.0)
    roll_weights = pd.DataFrame(
        np.zeros((len(dates), len(contracts))),
        index=dates,
        columns=contracts
    )
    prev_date = roll_weights.index[0]

    # Loop through each contract and create the specific weightings for 
    # each contract depending upon the settlement date and rollover days
    for i, (item, ex_date) in enumerate(expiry_dates.iteritems()):
        if i < len(expiry_dates) - 1:
            roll_weights.ix[prev_date:ex_date - pd.offsets.BDay(), item] = 1
            roll_range = pd.date_range(
                end=ex_date - pd.offsets.BDay(),
                periods=rollover_days + 1,
                freq='B'
            )

            # Create a sequence of roll weights (i.e. [0.0, 0.2, ..., 0.8, 1.0])
            # and use these to adjust the weightings of each future
            decay_weights = np.linspace(0, 1, rollover_days + 1)
            roll_weights.ix[roll_range, item] = 1 - decay_weights
            roll_weights.ix[roll_range, expiry_dates.index[i + 1]] = decay_weights
        else:
            roll_weights.ix[prev_date:, item] = 1

        prev_date = ex_date

    return roll_weights

if __name__ == "__main__":
    # Download the current Front and Back (near and far) futures contracts
    # for WTI Crude, traded on NYMEX, from Quandl.com. You will need to adjust
    # the contracts to reflect your current near/far contracts depending upon
    # the point at which you read this!
    api_key = os.environ['QUANDL_API_KEY']
    wti_near = quandl.get("ICE/TF2016", authtoken=api_key)
    wti_far = quandl.get("ICE/TG2016", authtoken=api_key)
    wti = pd.DataFrame(
        {"TF2016": wti_near['Settle'], "TG2016": wti_far['Settle']},
        index=wti_far.index
    )

    # Create the dictionary of expiry dates for each contract
    expiry_dates = pd.Series({
        "TF2016": datetime.datetime(2015, 12, 19),
        "TG2016": datetime.datetime(2016, 2, 21)
    }).order()

    # Obtain the rollover weighting matrix/DataFrame
    weights = futures_rollover_weights(
        wti_near.index[0],
        expiry_dates,
        wti.columns
    )

    # Construct the continuous future of the WTI contracts
    wti_continuous = (wti * weights).sum(1).dropna()

    # Output the merged series of contract settle prices
    print wti_continuous.tail(60)
