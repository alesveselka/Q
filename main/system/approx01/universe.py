#!/usr/bin/python

import os
import MySQLdb as mysql


class Universe(object):
    """
    Encapsulates investment universe
    """
    def __init__(self, name):
        self._name = name
        self._markets = []

    def markets(self):
        connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        cursor = connection.cursor()

        cursor.execute("""
            SELECT market_ids
            FROM investment_universe
            WHERE name = '%s';
        """ % self._name)
        market_ids = cursor.fetchone()[0]

        print market_ids[0]

        cursor.execute("""
            SELECT m.name, m.code, m.currency, m.first_data_date, g.name as group_name
            FROM market as m INNER JOIN  `group` as g ON m.group_id = g.id
            WHERE m.id = '%s';
        """ % market_ids[0])

        markets = cursor.fetchall()
        print markets

        # sql = """SELECT
        #         market_ids,
        #         dp.open_price,
        #         dp.high_price,
        #         dp.low_price,
        #         # dp.adj_close_price,
        #         dp.close_price,
        #         dp.volume,
        #         sym.name
        #      FROM symbol AS sym INNER JOIN daily_price as dp ON dp.symbol_id = sym.id
        #      WHERE sym.ticker = '%s'
        #      # AND dp.price_date > '20150101'
        #      # AND dp.price_date < '20140228'
        #      ORDER BY dp.price_date ASC;""" % request.args["symbol"]
        #
        # # TODO try-except and return error to FE
        #
        # cursor = connection.cursor()
        # cursor.execute(sql)
        # data = cursor.fetchall()
        #
        # return jsonify([(
        #                     millis(d[0]),           # datetime
        #                     float(d[1]),            # open
        #                     float(d[2]),            # high
        #                     float(d[3]),            # low
        #                     float(d[4]),            # close
        #                     float(d[5]),            # volume
        #                     d[6]) for d in data])   # name
