#!/usr/bin/python

import os
import datetime as dt
import MySQLdb as mysql
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


def market_series(market_id, start_date, end_date):
    codes = __market_codes(market_id)
    code = ''.join([codes[1], '2']) if 'C' in codes[2] else codes[1]
    cursor = connection.cursor()
    continuous_query = """
            SELECT price_date, settle_price
            # FROM continuous_spliced
            FROM continuous_adjusted
            WHERE market_id = '%s'
            AND code = '%s'
            AND roll_strategy_id = 2
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
    cursor.execute(continuous_query % (
        market_id,
        code,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    ))
    return cursor.fetchall()


def __stdev(values):
    length = len(values)
    mean = sum(values) / length
    return sqrt(sum((v - mean)**2 for v in values) / (length - 1))


def __volatility_series(price_series, lookback):
    """
    Return calculated volatility
    
    :param price_series:    price series to calculate volatility on
    :param lookback:        lookback number for the vol. calculation
    :return:                list of tuples(date, price, return, stdev, volatility)
    """
    smooth_factor = 5
    returns = []
    stdevs = []
    devs = []
    devs_squared = []
    result = [(price_series[0][0], price_series[0][1], 0.0, 0.0, 0.0, 0.0)]
    # TODO also calculate movement vol.
    for i, item in enumerate(price_series[smooth_factor:]):
        price = item[1]
        prev_price = price_series[i][1]
        ret = abs(price / prev_price - 1)
        returns.append(ret * -1 if price < prev_price else ret)
        return_window = returns[-lookback:]
        devs.append(return_window[-1] - sum(return_window) / len(return_window))
        devs_squared.append(devs[-1] ** 2)
        vol = sqrt(sum(devs_squared[-lookback:]) / (lookback - 1)) if i >= lookback - 1 else 0.0
        # print item[0], i, len(return_window), devs[-1], devs_squared[-1], vol

        # stdevs.append(__stdev(returns[-lookback:]) if i else 0.0)
        # vol = sqrt(sum(stdevs[-lookback:]) / (lookback-1)) if i >= lookback - 1 else 0.0
        result.append((item[0], price, returns[-1], devs[-1], devs_squared[-1], vol))

    return result


# def __correlations(market_id1, market_id2):


def main():
    investment_universe = __investment_universe('25Y')
    start_date = dt.date(1900, 1, 1)
    end_date = dt.date(9999, 12, 31)
    market_ids = investment_universe[2].split(',')
    market_id_pairs = [c for c in combinations(map(int, market_ids), 2)]

    # W = 33
    # KW = 25
    # MW = 27
    # SP = 55
    # TU = 79

    lookback = 25
    volas = {}
    # for market_id in market_ids:
    for market_id in [55]:
        print 'calculating', market_id
        price_series = market_series(market_id, dt.date(2007, 1, 3), dt.date(2007, 12, 31))
        # price_series = market_series(market_id, start_date, end_date)
        volas[market_id] = __volatility_series(price_series, lookback)

        # for p in price_series[5:30]:
        #     print p

    # for v in volas[27]:
    #     print v

    # for pair in market_id_pairs:
    # for pair in [(55, 79)]:


if __name__ == '__main__':
    main()
