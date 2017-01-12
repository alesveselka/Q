#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import warnings

import MySQLdb as mdb
import requests

# Connect to the MySQL instance
db_host = 'localhost'
db_user = 'sec_user'
db_pass = 'root'        # Load from ENVs
db_name = 'securities_master'
connection = mdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)

def obtain_list_of_db_tickers():
    """
    Obtain a list of the ticker symbols in the database
    """

    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, ticker FROM symbol")
        data = cursor.fetchall()
        return [(d[0], d[1]) for d in data]

if __name__ == "__main__":
    # print(obtain_list_of_db_tickers())
