#!/usr/bin/python

import os
import datetime as dt
import MySQLdb as mysql
from math import log
from math import sqrt
from itertools import combinations


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


def __market_codes(market_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT name, code, data_codes
        FROM market
        WHERE id = '%s';
    """ % market_id)
    return cursor.fetchone()


def market_series(market_id, roll_strategy_id, start_date, end_date):
    codes = __market_codes(market_id)
    code = ''.join([codes[1], '2']) if 'C' in codes[2] else codes[1]
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
        code,
        roll_strategy_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    ))
    return cursor.fetchall()


def __std(values):
    length = len(values)
    mean = sum(values) / length
    return sqrt(sum((v - mean)**2 for v in values) / (length - 1))


def __volatility_series(price_series, lookback):
    log_returns = []
    returns_squared = []
    result = [price_series[0]]
    for i, item in enumerate(price_series[1:]):
        price = item[1]
        log_returns.append(log(price / price_series[i][1]))
        returns_squared.append(log_returns[-1] ** 2)
        std = __std(log_returns[-lookback:]) if i else 0.0
        vol = sqrt(sum(returns_squared[-lookback:]) / lookback) if i >= lookback - 1 else 0.0
        result.append((item[0], price, log_returns[-1], returns_squared[-1], vol, std))

    return result


# def __correlations(market_id1, market_id2):


def main():
    # roll_strategy = __roll_strategy('standard_roll_1')
    roll_strategy = __roll_strategy('norgate')
    investment_universe = __investment_universe('25Y')
    start_contract_date = investment_universe[0]
    start_data_date = investment_universe[1]
    start_date = dt.date(1900, 1, 1)
    end_date = dt.date(9999, 12, 31)
    market_ids = investment_universe[2].split(',')
    # markets = __market_codes(market_ids)
    series_w = market_series(33, roll_strategy[0], start_date, end_date)
    series_kw = market_series(25, roll_strategy[0], start_date, end_date)

    print 'start_contract_date', investment_universe

    # print len(series_w)
    # for s in series_w[:10]:
    #     print s

    # print len(series_kw)
    # for s in series_kw[:10]:
    #     print s

    # print 'std: ', __std([-0.00031358, 0.00265584])

    market_id_pairs = [c for c in combinations(map(int, market_ids), 2)]

    # for pair in market_id_pairs:
    #     print pair

    # print market_ids
    print len(market_ids)
    print len(market_id_pairs)

    price_series = market_series(55, roll_strategy[0], dt.date(2007, 1, 3), dt.date(2008, 12, 31))
    # __volatility_series(33, roll_strategy[0], start_date, end_date, 25)
    __volatility_series(price_series, 25)


if __name__ == '__main__':
    main()
