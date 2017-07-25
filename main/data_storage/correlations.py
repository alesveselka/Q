#!/usr/bin/python

import os
import sys
import time
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
volatility = {}
correlation = {}


def log(message, code='', index=0, length=0.0, complete=False):
    sys.stdout.write('%s\r' % (' ' * 80))
    if complete:
        sys.stdout.write('%s complete\r\n' % message)
    else:
        sys.stdout.write('%s %s (%d of %d) [%d %%]\r' % (message, code, index, length, index / length * 100))
    sys.stdout.flush()
    return True


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


def __market_code(market_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT name, code, data_codes
        FROM market
        WHERE id = '%s';
    """ % market_id)
    codes = cursor.fetchone()
    return ''.join([codes[1], '2']) if 'C' in codes[2] else codes[1]


def market_series(market_id, market_code, start_date, end_date):
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
        market_code,
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


def calculate_volatility(market_id, market_code, start_date, end_date, lookback):
    """
    Calculate volatility for market specified by the id passed in
    
    :param market_id:   ID of the market for which to calculate volatility
    :param market_code: Code symbol of the market instrument
    :param start_date:  starting date of calculation
    :param end_date:    end date of calculation
    :param lookback:    lookback window
    """
    price_series = market_series(market_id, market_code, start_date, end_date)
    volatility[market_id] = __volatility_series(price_series, lookback)


def calculate_correlation(market_id_a, market_id_b, lookback):
    """
    Calculate correlations between two markets which IDs are passed in
    
    :param market_id_a:     ID of first market
    :param market_id_b:     ID of second market
    :param lookback:        lookback window for the correlation calculation
    """
    DATE, PRICE, RETURN, DEVIATION, DEVIATION_SQUARED, DEVIATION_VOL, MOVEMENT_VOL = tuple(range(7))
    result = []
    indexes = {}

    vol_a, vol_a_indexes = volatility[market_id_a]
    vol_b, vol_b_indexes = volatility[market_id_b]
    first_date = max(vol_a[0][0], vol_b[0][0])
    last_date = min(vol_a[-1][0], vol_b[-1][0])
    date_range = [first_date + dt.timedelta(days=i) for i in xrange(0, (last_date - first_date).days + 1)]
    for i, date in enumerate(date_range):
        if date in vol_a_indexes and date in vol_b_indexes:
            index_a = vol_a_indexes[date]
            index_b = vol_b_indexes[date]
            if vol_a[index_a][DEVIATION_VOL] and vol_b[index_b][DEVIATION_VOL]:
                return_sum = sum(r[0] * r[1] for r in zip(
                    [v[RETURN] for v in vol_a[index_a-lookback+1:index_a+1]],
                    [v[RETURN] for v in vol_b[index_b-lookback+1:index_b+1]]
                ))
                deviation_sum = sum(d[0] * d[1] for d in zip(
                    [v[DEVIATION] for v in vol_a[index_a-lookback+1:index_a+1]],
                    [v[DEVIATION] for v in vol_b[index_b-lookback+1:index_b+1]]
                ))
                move_vol_a = vol_a[index_a][MOVEMENT_VOL]
                move_vol_b = vol_b[index_b][MOVEMENT_VOL]
                dev_vol_a = vol_a[index_a][DEVIATION_VOL]
                dev_vol_b = vol_b[index_b][DEVIATION_VOL]
                movement_corr = return_sum / (lookback * move_vol_a * move_vol_b) if move_vol_a and move_vol_b else 0.0
                deviation_corr = deviation_sum / ((lookback - 1) * dev_vol_a * dev_vol_b) if dev_vol_a and dev_vol_b else 0.0

                result.append((date, movement_corr, deviation_corr))
                indexes[date] = len(result) - 1

    correlation['%s_%s' % (market_id_a, market_id_b)] = result, indexes


def main():
    start = time.time()
    investment_universe = __investment_universe('25Y')
    start_date = dt.date(2007, 1, 1)#dt.date(1900, 1, 1)
    end_date = dt.date(2007, 12, 31)#dt.date(9999, 12, 31)
    # market_ids = investment_universe[2].split(',')
    market_ids = ['55','79', '9']
    market_id_pairs = [c for c in combinations(map(str, market_ids), 2)]
    market_codes = {market_id: __market_code(market_id) for market_id in market_ids}
    lookback = 25

    msg = 'Calculating volatility'
    length = float(len(market_ids))
    map(lambda i: log(msg, i[1], i[0], length)
                  and calculate_volatility(i[1], market_codes[i[1]], start_date, end_date, lookback), enumerate(market_ids))

    msg = 'Calculating correlation'
    length = float(len(market_id_pairs))
    map(lambda i: log(msg, i[1], i[0], length)
                  and calculate_correlation(i[1][0], i[1][1], lookback), enumerate(market_id_pairs))

    log(msg, index=int(length), length=length, complete=True)

    print 'Time:', time.time() - start, (time.time() - start) / 60


if __name__ == '__main__':
    main()
