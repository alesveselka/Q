#!/usr/bin/python

import os
import MySQLdb as mysql


connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)


def __roll_strategy(name):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `roll_strategy` WHERE name = '%s'" % name)
    return cursor.fetchone()


def __investment_universe(name):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT contract_start_date, data_start_date, market_ids
        FROM investment_universe
        WHERE name = '%s';
    """ % name)
    return cursor.fetchone()


def __markets(market_ids):
    cursor = connection.cursor()
    market_query = """
        SELECT name, code, data_codes
        FROM market
        WHERE id = '%s';
    """
    market_data = []
    for market_id in market_ids():
        cursor.execute(market_query % market_id)
        market_data.append(cursor.fetchone())

    return market_data


def main():
    investment_universe = __investment_universe('25Y')
    market_ids = investment_universe[2].split(',')
    roll_strategy = __roll_strategy('standard_roll_1')

    print roll_strategy


if __name__ == '__main__':
    main()
