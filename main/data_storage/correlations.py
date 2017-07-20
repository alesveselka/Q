#!/usr/bin/python

import os
import datetime as dt
import MySQLdb as mysql


connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)


def __roll_strategy(name):
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, type, params FROM `roll_strategy` WHERE name = '%s'" % name)
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
    for market_id in market_ids:
        cursor.execute(market_query % market_id)
        market_data.append(cursor.fetchone())

    return market_data


def market_series(market_id, market_code, roll_strategy_id, start_date, end_date):
    cursor = connection.cursor()
    continuous_query = """
            SELECT price_date, settle_price
            FROM continuous_adjusted
            WHERE market_id = '%s'
            AND code = '%s'
            AND roll_strategy_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
    cursor.execute(continuous_query % (
        market_id,
        market_code,
        roll_strategy_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    ))
    return cursor.fetchall()


def main():
    roll_strategy = __roll_strategy('standard_roll_1')
    investment_universe = __investment_universe('25Y')
    start_contract_date = investment_universe[0]
    start_data_date = investment_universe[1]
    end_date = dt.date(2015, 12, 31)
    market_ids = investment_universe[2].split(',')
    markets = __markets(market_ids)
    series = market_series(33, 'W2', roll_strategy[0], start_contract_date, end_date)

    print len(series)
    for s in series[-10:]:
        print s


if __name__ == '__main__':
    main()
