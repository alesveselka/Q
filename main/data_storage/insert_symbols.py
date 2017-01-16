#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
from math import ceil

import bs4
import MySQLdb as mdb
import requests

def obtain_parse_wiki_snp500():
    """
    Download and parse the Wikipedia list of S&P 500
    constituents using 'requests' and 'BeautifulSoup'.

    Returns a list of tuples for to add to MySQL.
    """

    # stores the curent time, for 'created_at' record
    now = datetime.datetime.utcnow()

    # use 'requests' and 'BeautifulSoup' to download the 
    # list of S&P 500 companies and obtain the  symbol table
    response = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    # this selects the first table, using CSS Selector syntax
    # and then  ignores the header row ([1:])
    symbolslist = soup.select('table')[0].select('tr')[1:]

    # obtain the sy,bol information for each row
    # in the S&P500  constituent table
    symbols = []
    for i, symbol in enumerate(symbolslist):
        tds = symbol.select('td')
        symbols.append((
            tds[0].select('a')[0].text,     # Ticker
            'stock',                        # Instrument
            tds[1].select('a')[0].text,     # Name
            tds[3].text,                    # Sector
            'USD',                          # Currency
            now,                            # Created date
            now                             # Last updated dat
            ))

    return symbols

def insert_snp500_symbols(symbols):
    """
    Insert the S&P 500 symols into MySQL database.
    """

    # Connect to the MySQL instance
    db_host = 'localhost'
    db_user = 'sec_user'
    db_pass = 'root'        # Load from ENVs
    db_name = 'securities_master'
    connection = mdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)

    # Create the insert strings
    column_str = "ticker, instrument, name, sector, currency, created_date, last_updated_date"
    insert_str = ("%s, " * 7)[:-2]
    final_str = "INSERT INTO symbol (%s) VALUES (%s)" % (column_str, insert_str)

    # Using the MySQL connection, carry out
    # an INSERT INTO for every symbol
    with connection:
        cursor = connection.cursor()
        cursor.executemany(final_str, symbols)

if __name__ == "__main__":
    insert_snp500_symbols(obtain_parse_wiki_snp500())
