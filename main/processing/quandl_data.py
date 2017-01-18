#!/usr/bin/python
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import pandas as pd
import requests
import os

def construct_futures_symbols(symbol, start_year=2010, end_year=2016):
    """
    Construct a list of futures contract doces
    for a particular symbol and timeframe.
    """
    futures = []

    # March, June, Sepetember and December delivery codes
    months = 'HMUZ'
    for y in range(start_year, end_year+1):
        for m in months:
            futures.append("%s%s%s" % (symbol, m, y))

    return futures

def download_contract_from_quandl(contract, api_key, download_dir):
    """
    Download an individual futures contract from Quandl and then
    store it to disk in the 'download_dir' directory. An 'auth_token' is 
    required, which is obtained from Quandl upon sign-up.
    """
    # Constrcut the API call from the contract and auth_token
    api_call = "https://www.quandl.com/api/v1/datasets/CME/%s.csv?api_key=%s" % (contract, api_key)

    # Download data from Quandl
    data = requests.get(api_call).text

    # Store the data to disk
    fc = open('%s/%s.csv' % (download_dir, contract), 'w')
    fc.write(data)
    fc.close()

def download_historical_contracts(symbol, api_key, download_dir, start_year=2010, end_year=2016):
    """
    Download all futures contracts  for a specified symbol
    between a start_year and end_year.
    """
    contracts = construct_futures_symbols(symbol, start_year, end_year)
    for c in contracts:
        print "Downloading contract: %s" % c
        download_contract_from_quandl(c, api_key, download_dir)

if __name__ == "__main__":
    symbol = 'ES'
    api_key = os.environ['QUANDL_API_KEY']
    download_dir = '../../Downloads/quandl/futures/ES' # Make sure the directory exists!
    start_year = 2010
    end_year = 2016

    # Download the contracts data into directory
    download_historical_contracts(symbol, api_key, download_dir, start_year, end_year)

    # Open up a single contract via  'read_csv'
    # and plot the settle price
    es = pd.io.parsers.read_csv("%s/ESH2010.csv" % download_dir, index_col="Date")
    es['Settle'].plot()
    plt.show()
