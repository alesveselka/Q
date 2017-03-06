#!/usr/bin/python

import os
import MySQLdb as mysql

from event_dispatcher import EventDispatcher


class InvestmentUniverse(EventDispatcher):
    """
    Encapsulates investment universe
    """
    def __init__(self, name):
        super(InvestmentUniverse, self).__init__()

        self._name = name
        self._markets = []

    def _market_ids(self, cursor):
        cursor.execute("SELECT market_ids FROM investment_universe WHERE name = '%s';" % self._name)
        return cursor.fetchone()[0].split(',')

    def markets(self):
        # TODO cache requests
        connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        cursor = connection.cursor()
        sql = """
            SELECT m.name, m.code, m.currency, m.first_data_date, g.name as group_name
            FROM market as m INNER JOIN  `group` as g ON m.group_id = g.id
            WHERE m.id = '%s';
        """

        for id in self._market_ids(cursor):
            cursor.execute(sql % id)
            self._markets.append(cursor.fetchone())

        return self._markets
