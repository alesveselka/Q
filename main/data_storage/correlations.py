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
    :return:                tuple of list of tuples(
                                date
                                price, 
                                return, 
                                deviation, 
                                deviation-squared, 
                                deviation-volatility, 
                                movement-volatility
                            ), and dict of indexes
    """
    smooth_factor = 5
    returns = []
    deviations = []
    deviations_squared = []
    result = [(price_series[0][0], price_series[0][1], None, None, None, None, None)]
    indexes = {price_series[0][0]: 0}
    for i, item in enumerate(price_series[smooth_factor:]):
        price = item[1]
        prev_price = price_series[i][1]
        ret = abs(price / prev_price - 1)
        returns.append(ret * -1 if price < prev_price else ret)
        return_window = returns[-lookback:]
        deviations.append(return_window[-1] - sum(return_window) / len(return_window))
        deviations_squared.append(deviations[-1]**2)
        deviation_vol = sqrt(sum(deviations_squared[-lookback:]) / (lookback - 1)) if i >= lookback - 1 else None
        movement_vol = sqrt(sum(r**2 for r in return_window) / lookback) if i >= lookback - 1 else None
        result.append((item[0], price, returns[-1], deviations[-1], deviations_squared[-1], deviation_vol, movement_vol))
        indexes[item[0]] = len(result) - 1

    return result, indexes


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

    start_date = dt.date(2007, 1, 3)
    end_date = dt.date(2008, 12, 31)
    lookback = 25
    volas = {}
    # for market_id in market_ids:
    for market_id in [55, 79]:
        print 'calculating volatility', market_id
        price_series = market_series(market_id, start_date, end_date)
        volas[market_id] = __volatility_series(price_series, lookback)

    date_range = [start_date + dt.timedelta(days=i) for i in xrange(0, (end_date - start_date).days + 1)]
    DATE = 0
    PRICE = 1
    RETURN = 2
    DEVIATION = 3
    DEVIATION_SQUARED = 4
    DEVIATION_VOL = 5
    MOVEMENT_VOL = 6

    # for pair in market_id_pairs:
    for pair in [(55, 79)]:
        print 'calculating correlation', pair
        vol_a, vol_a_indexes = volas[pair[0]]
        vol_b, vol_b_indexes = volas[pair[1]]

        for i, date in enumerate(date_range):
            if date in vol_a_indexes and vol_a[vol_a_indexes[date]][DEVIATION_VOL] and date in vol_b_indexes and vol_b[vol_b_indexes[date]][DEVIATION_VOL]:
            # vol_a_record = [v for v in vol_a if v[DATE] == date]
            # vol_b_record = [v for v in vol_a if v[DATE] == date]
            # if date in vol_a and vol_a[date][DEVIATION_VOL] and date in vol_b and vol_b[date][DEVIATION_VOL]:
            # if len(vol_a_record) and vol_a_record[0][DEVIATION_VOL] and len(vol_b_record) and vol_b_record[0][DEVIATION_VOL]:

                index_a = vol_a_indexes[date] + 1
                index_b = vol_b_indexes[date] + 1
                returns_a = [v[RETURN] for v in vol_a[index_a-lookback:index_a]]
                returns_b = [v[RETURN] for v in vol_b[index_b-lookback:index_b]]

                movement_correlation = sum(r[0] * r[1] for r in zip(returns_a, returns_b)) / (lookback * vol_a[vol_a_indexes[date]][MOVEMENT_VOL] * vol_b[vol_b_indexes[date]][MOVEMENT_VOL])

                print i, date, movement_correlation


if __name__ == '__main__':
    main()
