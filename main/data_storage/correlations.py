#!/usr/bin/python

import os
import sys
import time
import json
import datetime as dt
import MySQLdb as mysql
from math import sqrt
from itertools import combinations
from collections import defaultdict


connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)
market_volatility = {}
market_correlation = {}
group_volatility = ()
group_correlation = ()


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


def __group_id(market_id):
    cursor = connection.cursor()
    cursor.execute("SELECT group_id FROM `market` WHERE id = '%s';" % market_id)
    return cursor.fetchone()


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


def calculate_volatility(market_id, market_code, start_date, end_date, lookback):
    """
    Calculate volatility for market specified by the id passed in.
    Result is tuple of list of tuples(
        date, price, return, deviation, deviation-squared, deviation-volatility, movement-volatility
    ), and dict of indexes
    
    :param market_id:   ID of the market for which to calculate volatility
    :param market_code: Code symbol of the market instrument
    :param start_date:  starting date of calculation
    :param end_date:    end date of calculation
    :param lookback:    lookback window
    """
    price_series = market_series(market_id, market_code, start_date, end_date)
    smooth_factor = 5
    returns = []
    deviations = []
    deviations_squared = []
    result = [(price_series[0][0], price_series[0][1], None, None, None, None, None)]
    indexes = {price_series[0][0]: 0}
    for i, item in enumerate(price_series[smooth_factor:]):
        price = item[1]
        prev_price = price_series[i][1]
        # TODO correct spikes on roll-days
        ret = abs(price / prev_price - 1)
        returns.append(ret * -1 if price < prev_price else ret)
        return_window = returns[-lookback:]
        deviations.append(return_window[-1] - sum(return_window) / len(return_window))
        deviations_squared.append(deviations[-1]**2)
        deviation_vol = sqrt(sum(deviations_squared[-lookback:]) / (lookback - 1)) if i >= lookback - 1 else None
        movement_vol = sqrt(sum(r**2 for r in return_window) / lookback) if i >= lookback - 1 else None
        result.append((item[0], price, returns[-1], deviations[-1], deviations_squared[-1], deviation_vol, movement_vol))
        indexes[item[0]] = len(result) - 1

    market_volatility[market_id] = result, indexes


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

    vol_a, vol_a_indexes = market_volatility[market_id_a]
    vol_b, vol_b_indexes = market_volatility[market_id_b]
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

    market_correlation['%s_%s' % (market_id_a, market_id_b)] = result, indexes


def calculate_group_volatility(market_ids, groups, start_date, end_date, lookback):
    """
    Calculate group volatility as averages of markets volatility in each group
     
    :param market_ids:  IDs of markets
    :param groups:      dict of market IDs and associated group IDs
    :param start_date:  start date of the series
    :param end_date:    end date of the series
    :param lookback:    lookback window
    """
    DATE, PRICE, RETURN, DEVIATION, DEVIATION_SQUARED, DEVIATION_VOL, MOVEMENT_VOL = tuple(range(7))
    result = []
    indexes = {}
    date_range = [start_date + dt.timedelta(days=i) for i in xrange(0, (end_date - start_date).days + 1)]
    for i, date in enumerate(date_range):
        returns = defaultdict(list)
        mov_volas = defaultdict(list)
        dev_volas = defaultdict(list)
        for market_id in market_ids:
            group_id = groups[market_id]
            vol, vol_indexes = market_volatility[market_id]
            if date in vol_indexes:
                if vol[vol_indexes[date]][RETURN]:
                    returns[group_id].append(vol[vol_indexes[date]][RETURN])
                if vol[vol_indexes[date]][MOVEMENT_VOL]:
                    mov_volas[group_id].append(vol[vol_indexes[date]][MOVEMENT_VOL])
                if vol[vol_indexes[date]][DEVIATION_VOL]:
                    dev_volas[group_id].append(vol[vol_indexes[date]][DEVIATION_VOL])

        group_returns = {k: sum(returns[k]) for k in returns.keys()}
        deviations = {}
        for k in group_returns.keys():
            result_window = result[-(lookback-1):]
            last_returns = [r[1][k] for r in result_window if k in r[1]] + [group_returns[k]]
            deviations[k] = group_returns[k] - sum(last_returns) / len(last_returns)

        result.append((
            date,
            group_returns,
            deviations,
            {k: sum(mov_volas[k]) / len(mov_volas[k]) for k in mov_volas.keys()},
            {k: sum(dev_volas[k]) / len(dev_volas[k]) for k in dev_volas.keys()}
        ))
        indexes[date] = len(result) - 1

    group_volatility = result, indexes


def aggregate_values(market_ids, market_codes, lookback):
    """
    Aggregate volatility, correlation and other values for inserting to the DB
    
    :param market_ids:      list of market IDs
    :param market_codes:    dict of market IDs as keys and market codes as values
    :param lookback:        lookback window used for calculating the values
    :return:                list of tuples(market_id, market_code, lookback, date, move_vol, dev_vol, move_corr, dev_corr)
    """
    msg = 'Aggregating values'
    length = float(len(market_ids))

    DEVIATION_VOL, MOVEMENT_VOL, MOVEMENT_CORR, DEVIATION_CORR = tuple([5, 6, 1, 2])
    values = []
    corr_keys = market_correlation.keys()
    for i, market_id in enumerate(market_ids):
        market_code = market_codes[market_id]
        log(msg, market_code, i, length)

        vol, vol_indexes = market_volatility[market_id]
        pairs = [k for k in corr_keys if market_id in k.split('_')]
        other_ids = filter(lambda i: i != market_id, reduce(lambda r, p: r + p.split('_'), pairs, []))
        for date in sorted(vol_indexes.keys()):
            v = vol[vol_indexes[date]]
            if v[MOVEMENT_VOL] and v[DEVIATION_VOL]:
                move_corrs = {}
                dev_corrs = {}
                for other_id in other_ids:
                    pair = [p for p in pairs if market_id in p.split('_') and other_id in p.split('_')][0]
                    corr, corr_index = market_correlation[pair]
                    move_corrs[other_id] = corr[corr_index[date]][MOVEMENT_CORR] if date in corr_index \
                        else (json.loads(values[-1][6])[other_id] if len(values) and int(market_id) == values[-1][0] else 0.0)
                    dev_corrs[other_id] = corr[corr_index[date]][DEVIATION_CORR] if date in corr_index \
                        else (json.loads(values[-1][7])[other_id] if len(values) and int(market_id) == values[-1][0] else 0.0)

                values.append((
                    int(market_id),
                    market_code,
                    lookback,
                    date,
                    v[MOVEMENT_VOL],
                    v[DEVIATION_VOL],
                    json.dumps(move_corrs),
                    json.dumps(dev_corrs)
                ))

    return values


def delete_values(lookback):
    connection.cursor().execute('DELETE FROM `market_correlation` WHERE lookback = %s' % lookback)


def insert_values(values):
    columns = [
        'market_id',
        'market_code',
        'lookback',
        'date',
        'movement_volatility',
        'dev_volatility',
        'movement_correlations',
        'dev_correlations'
    ]
    command = 'INSERT INTO `market_correlation` (%s) VALUES(%s)' % (', '.join(columns), ('%s, ' * len(columns))[:-2])

    with connection:
        cursor = connection.cursor()
        cursor.executemany(command, values)


def main(lookback):
    start = time.time()
    investment_universe = __investment_universe('25Y')
    # start_date = dt.date(1979, 1, 1)
    start_date = dt.date(2007, 1, 3)
    # end_date = dt.date(2017, 12, 31)
    end_date = dt.date(2007, 2, 20)
    # market_ids = investment_universe[2].split(',')
    market_ids = ['55','79']
    # market_ids = ['79', '80']
    market_id_pairs = [c for c in combinations(map(str, market_ids), 2)]
    market_codes = {market_id: __market_code(market_id) for market_id in market_ids}
    groups = {market_id: __group_id(market_id)[0] for market_id in market_ids}

    msg = 'Calculating volatility'
    length = float(len(market_ids))
    map(lambda i: log(msg, i[1], i[0], length)
                  and calculate_volatility(i[1], market_codes[i[1]], start_date, end_date, lookback), enumerate(market_ids))

    msg = 'Calculating correlation'
    length = float(len(market_id_pairs))
    map(lambda i: log(msg, i[1], i[0], length)
                  and calculate_correlation(i[1][0], i[1][1], lookback), enumerate(market_id_pairs))

    calculate_group_volatility(market_ids, groups, start_date, end_date, lookback)

    log(msg, index=int(length), length=length, complete=True)

    # msg = 'Aggregating values'
    # values = aggregate_values(market_ids, market_codes, lookback)
    # log(msg, index=len(market_ids), length=float(len(market_ids)), complete=True)
    #
    # msg = 'Inserting values'
    # length = float(len(values))
    # block = int(length / 10)
    # delete_values(lookback)
    # for i in range(10 + 1):
    #     log(msg, '', i, length)
    #     insert_values(values[i*block:(i+1)*block])
    # log(msg, index=int(length), length=length, complete=True)
    #
    # print 'Time:', time.time() - start, (time.time() - start) / 60


if __name__ == '__main__':
    main(25)
