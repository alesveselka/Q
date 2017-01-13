#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import pandas as pd
import MySQLdb as mdb

if __name__ == "__main__":
    # Connect to the MySQL instance
    db_host = 'localhost'
    db_user = 'sec_user'
    db_pass = 'root'        # Load from ENVs
    db_name = 'securities_master'
    connection = mdb.connect(db_host, db_user, db_pass, db_name)

    # Select all of the historic Google adjusted close data
    sql = """SELECT dp.price_date, dp.adj_close_price 
             FROM symbol AS sym 
             INNER JOIN daily_price as dp 
             ON dp.symbol_id = sym.id 
             WHERE sym.ticker = 'GOOG' 
             ORDER BY dp.price_date ASC;"""