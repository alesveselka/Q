#!/usr/bin/python

import os
import sys
import time
import json
import datetime as dt
import MySQLdb as mysql
from math import sqrt
from itertools import combinations
from itertools import groupby
from operator import itemgetter
from collections import defaultdict
from collections import deque

ew_const = 2.0 / (36 + 1)
connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)
market_volatility = {}
market_correlation = {}
group_volatility = []
group_volatility_indexes = {}
group_correlation = {}


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
            FROM continuous_spliced
            # FROM continuous_adjusted
            WHERE market_id = '%s'
            AND code = '%s'
            # AND roll_strategy_id = 2
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
        variance = sum(deviations_squared[-lookback:]) / (lookback - 1) if i >= lookback - 1 else None
        # TODO annualize
        # TODO standardize the VOLs for comparable correlations
        deviation_vol = sqrt(variance) if variance else None
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
                movement_corr = return_sum / (lookback * move_vol_a * move_vol_b) if move_vol_a and move_vol_b \
                    else (result[-1][1] if len(result) else 0.0)
                last = result[-1][3] if len(result) else movement_corr
                movement_corr_ew = (ew_const * movement_corr) + (1 - ew_const) * last

                deviation_corr = deviation_sum / ((lookback - 1) * dev_vol_a * dev_vol_b) if dev_vol_a and dev_vol_b \
                    else (result[-1][2] if len(result) else 0.0)
                last = result[-1][4] if len(result) else movement_corr
                deviation_corr_ew = (ew_const * deviation_corr) + (1 - ew_const) * last

                result.append((date, movement_corr, deviation_corr, movement_corr_ew, deviation_corr_ew))
                indexes[date] = len(result) - 1

    market_correlation['%s_%s' % (market_id_a, market_id_b)] = result, indexes


def calculate_group_volatility(market_ids, groups, lookback):
    """
    Calculate group volatility as averages of markets volatility in each group
     
    :param market_ids:  IDs of markets
    :param groups:      dict of market IDs and associated group IDs
    :param lookback:    lookback window
    """
    msg = 'Calculating group volatility'

    DATE, PRICE, RETURN, DEVIATION, DEVIATION_SQUARED, DEVIATION_VOL, MOVEMENT_VOL = tuple(range(7))
    vol_dates = sorted(set(sum([market_volatility[m][1].keys() for m in market_ids], [])))
    date_range = [vol_dates[0] + dt.timedelta(days=i) for i in xrange(0, (vol_dates[-1] - vol_dates[0]).days + 1)]
    group_ids = set([groups[k] for k in groups.keys()])

    length = float(len(date_range))
    for i, date in enumerate(date_range):
        returns = defaultdict(list)
        mov_volas = defaultdict(list)
        dev_volas = defaultdict(list)
        for market_id in market_ids:
            group_id = groups[market_id]
            log(msg, group_id, i, length)

            vol, vol_indexes = market_volatility[market_id]
            if date in vol_indexes:
                if vol[vol_indexes[date]][RETURN]:
                    returns[group_id].append(vol[vol_indexes[date]][RETURN])
                if vol[vol_indexes[date]][MOVEMENT_VOL]:
                    mov_volas[group_id].append(vol[vol_indexes[date]][MOVEMENT_VOL])
                if vol[vol_indexes[date]][DEVIATION_VOL]:
                    dev_volas[group_id].append(vol[vol_indexes[date]][DEVIATION_VOL])

        if len(returns):
            group_returns = {g: (sum(returns[g]) / len(returns[g])) if g in returns else 0.0 for g in group_ids}
            deviations = {}
            for k in group_returns.keys():
                result_window = group_volatility[-(lookback-1):]
                last_returns = [r[1][k] for r in result_window if k in r[1]] + [group_returns[k]]
                deviations[k] = group_returns[k] - sum(last_returns) / len(last_returns)

            m_volas = {g: mov_volas[g] if g in mov_volas else (group_volatility[-1][5][g] if len(group_volatility) else [0.0]) for g in group_ids}
            d_volas = {g: dev_volas[g] if g in dev_volas else (group_volatility[-1][6][g] if len(group_volatility) else [0.0]) for g in group_ids}

            group_volatility.append([
                date,
                group_returns,
                deviations,
                {k: (sum(m_volas[k]) / len(m_volas[k])) if m_volas[k] else 0.0 for k in m_volas.keys()},
                {k: (sum(d_volas[k]) / len(d_volas[k])) if d_volas[k] else 0.0 for k in d_volas.keys()},
                mov_volas,
                dev_volas
            ])
            group_volatility_indexes[date] = len(group_volatility) - 1

    log(msg, index=int(length), length=length, complete=True)


def calculate_portfolio_volatility(market_ids, groups, lookback):
    """
    Calculate portfolio volatility
     
    :param market_ids:  IDs of markets
    :param groups:      dict of market IDs and associated group IDs
    :param lookback:    lookback window
    """
    msg = 'Calculating group volatility'

    DEVIATION_CORR = 2
    DATE, PRICE, RETURN, DEVIATION, DEVIATION_SQUARED, DEVIATION_VOL, MOVEMENT_VOL = tuple(range(7))
    vol_dates = sorted(set(sum([market_volatility[m][1].keys() for m in market_ids], [])))
    date_range = [vol_dates[0] + dt.timedelta(days=i) for i in xrange(0, (vol_dates[-1] - vol_dates[0]).days + 1)]
    group_ids = set([groups[k] for k in groups.keys()])
    grouped_market_ids = {i[0]: map(lambda l: l[0], i[1]) for i in groupby(sorted(groups.items(), key=itemgetter(1)), key=itemgetter(1))}
    corr_keys = market_correlation.keys()

    length = float(len(date_range))
    for i, date in enumerate(date_range):

        returns = defaultdict(list)
        deviations = defaultdict(list)
        volas = defaultdict(list)

        for group_id in group_ids:
            log(msg, group_id, i, length)

            group_market_ids = grouped_market_ids[group_id]
            weight = 1.0 / len(group_market_ids)
            group_market_id_pairs = list(combinations(group_market_ids, 2))

            terms = []
            for market_id in group_market_ids:
                market_vol, market_vol_indexes = market_volatility[market_id]
                # terms.append('W({0})^2 o({0})^2'.format(market_id))
                # print market_id, 'Market volatility:',market_vol[-1][DEVIATION_VOL]

                if date in market_vol_indexes:
                    dev = market_vol[market_vol_indexes[date]][DEVIATION if len(group_market_id_pairs) else DEVIATION_VOL]
                    terms.append(weight**2 * (dev**2 if dev else 0.0))  # TODO use prev value instead of zero

                    if date in market_vol_indexes:
                        if market_vol[market_vol_indexes[date]][RETURN]:
                            returns[group_id].append(market_vol[market_vol_indexes[date]][RETURN])

            for market_id_pair in group_market_id_pairs:
                pair_key = [k for k in corr_keys if market_id_pair[0] in k.split('_') and market_id_pair[1] in k.split('_')][0]
                market_1_vol, market_1_vol_indexes = market_volatility[market_id_pair[0]]
                market_2_vol, market_2_vol_indexes = market_volatility[market_id_pair[1]]
                corr, corr_indexes = market_correlation[pair_key]

                if date in market_1_vol_indexes and date in market_2_vol_indexes and date in corr_indexes:
                    # TODO use prev values instead of zeros
                    market_1_dev = market_1_vol[market_1_vol_indexes[date]][DEVIATION] if market_1_vol[market_1_vol_indexes[date]][DEVIATION] else 0.0
                    market_2_dev = market_2_vol[market_2_vol_indexes[date]][DEVIATION] if market_2_vol[market_2_vol_indexes[date]][DEVIATION] else 0.0
                    correlation = corr[corr_indexes[date]][DEVIATION_CORR] if corr[corr_indexes[date]][DEVIATION_CORR] else 0.0
                    # print pair_key, 'Market correlation:', corr[-1][DEVIATION_CORR]
                    # terms.append('2 * W({0}) * o({0}) * W({1}) * o({1}) * p({0}, {1})'.format(*market_id_pair))
                    terms.append(2 * weight * market_1_dev * weight * market_2_dev * correlation)

            deviations[group_id] = sum(terms)
            volas[group_id] = sqrt(abs(sum(terms)))

        if len(returns):
            group_returns = {g: (sum(returns[g]) / len(returns[g])) if g in returns else 0.0 for g in group_ids}

            group_volatility.append([
                date,
                group_returns,
                deviations,
                volas
            ])
            group_volatility_indexes[date] = len(group_volatility) - 1

    log(msg, index=int(length), length=length, complete=True)


def clean_group_volatility(groups):
    """
    Clean spikes in group volatility values due to inconsistent group market values
    
    Goes through group volatility list, check if recent volatility is value out of proportion of previous ones
    and eventually replace it with average of the surrounding values.
    
    :param groups: dict with keys of market IDs and values associated group IDs
    """
    MOVEMENT_VOL = 3
    DEVIATION_VOL = 4
    group_ids = set([groups[k] for k in groups.keys()])
    for i in range(3, len(group_volatility)-1):
        r = group_volatility[i-3:i+1]
        for vol_type in [MOVEMENT_VOL, DEVIATION_VOL]:
            for k in group_ids:
                vol_range = [v[vol_type][k] for v in r]
                max_range = max(vol_range) - min(vol_range)
                diffs = map(lambda i: abs(i[0][vol_type][k] - i[1][vol_type][k]) / max_range, zip(r[1:], r)) if max_range else tuple([1.0] * 3)
                sq = (diffs[1] * diffs[2]) if (diffs[1] * diffs[2]) else 1.0

                # Check if squared normalized difference is out of proportion
                if diffs[0] / sq and diffs[0] / sq < .1 and sq > .85:
                    group_volatility[i-1][vol_type][k] = r[-3][vol_type][k] + (r[-1][vol_type][k] - r[-3][vol_type][k]) / 2


def calculate_group_correlation(group_id_a, group_id_b, lookback):
    """
    Calculate correlations between two groups which IDs are passed in
    
    :param group_id_a:  first group ID for the calculation
    :param group_id_b:  second group ID for the calculation
    :param lookback:    lookback window for the correlation calculation
    """
    # TODO generalize together with 'calculate_correlation' function - mostly duplicate
    DATE, RETURNS, DEVIATIONS, MOVEMENT_VOL, DEVIATION_VOL = tuple(range(5))
    result = []
    indexes = {}
    lookback_window = deque([], lookback)

    for date in sorted(group_volatility_indexes):
        i = group_volatility_indexes[date]
        lookback_window.append(group_volatility[i])
        returns = [w[RETURNS] for w in lookback_window]
        move_vol = group_volatility[i][MOVEMENT_VOL]
        dev_vol = group_volatility[i][DEVIATION_VOL]
        if len(move_vol) and len(dev_vol):
            return_sum = sum(r[group_id_a] * r[group_id_b] for r in returns if group_id_a in r and group_id_b in r)
            move_vol_a = move_vol[group_id_a] if group_id_a in move_vol else None
            move_vol_b = move_vol[group_id_b] if group_id_b in move_vol else None
            movement_corr = return_sum / (lookback * move_vol_a * move_vol_b) if move_vol_a and move_vol_b \
                else (result[-1][1] if len(result) else 0.0)
            last = result[-1][3] if len(result) else movement_corr
            movement_corr_ew = (ew_const * movement_corr) + (1 - ew_const) * last

            deviations = [w[DEVIATIONS] for w in lookback_window]
            deviation_sum = sum(d[group_id_a] * d[group_id_b] for d in deviations if group_id_a in d and group_id_b in d)
            dev_vol_a = dev_vol[group_id_a] if group_id_a in dev_vol else None
            dev_vol_b = dev_vol[group_id_b] if group_id_b in dev_vol else None
            deviation_corr = deviation_sum / ((lookback - 1) * dev_vol_a * dev_vol_b) if dev_vol_a and dev_vol_b \
                else (result[-1][2] if len(result) else 0.0)
            last = result[-1][4] if len(result) else deviation_corr
            deviation_corr_ew = (ew_const * deviation_corr) + (1 - ew_const) * last

            result.append((date, movement_corr, deviation_corr, movement_corr_ew, deviation_corr_ew))
            indexes[date] = len(result) - 1

    group_correlation['%s_%s' % (group_id_a, group_id_b)] = result, indexes


def calculate_portfolio_correlation(group_id_a, group_id_b, lookback):
    """
    Calculate correlations between two groups which IDs are passed in
    
    :param group_id_a:  first group ID for the calculation
    :param group_id_b:  second group ID for the calculation
    :param lookback:    lookback window for the correlation calculation
    """
    # TODO generalize together with 'calculate_correlation' function - mostly duplicate
    DATE, RETURNS, DEVIATIONS, DEVIATION_VOL = tuple(range(4))
    result = []
    indexes = {}
    lookback_window = deque([], lookback)

    for date in sorted(group_volatility_indexes):
        i = group_volatility_indexes[date]
        lookback_window.append(group_volatility[i])
        dev_vol = group_volatility[i][DEVIATION_VOL]
        if len(dev_vol):
            deviations = [w[DEVIATIONS] for w in lookback_window]
            deviation_sum = sum(d[group_id_a] * d[group_id_b] for d in deviations if group_id_a in d and group_id_b in d)
            dev_vol_a = dev_vol[group_id_a] if group_id_a in dev_vol else None
            dev_vol_b = dev_vol[group_id_b] if group_id_b in dev_vol else None
            deviation_corr = deviation_sum / ((lookback - 1) * dev_vol_a * dev_vol_b) if dev_vol_a and dev_vol_b \
                else (result[-1][1] if len(result) else 0.0)

            result.append((date, deviation_corr))
            indexes[date] = len(result) - 1

    group_correlation['%s_%s' % (group_id_a, group_id_b)] = result, indexes


def aggregate_market_values(market_ids, market_codes, lookback):
    """
    Aggregate volatility, correlation and other values for inserting to the DB
    
    :param market_ids:      list of market IDs
    :param market_codes:    dict of market IDs as keys and market codes as values
    :param lookback:        lookback window used for calculating the values
    :return:                list of tuples(market_id, market_code, lookback, date, move_vol, dev_vol, move_corr, dev_corr)
    """
    msg = 'Aggregating market values'
    length = float(len(market_ids))

    MOVEMENT_CORR, DEVIATION_CORR, MOVEMENT_CORR_EW, DEVIATION_CORR_EW, DEVIATION_VOL, MOVEMENT_VOL = (1, 2, 3, 4, 5, 6)
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
                move_corrs_ew = {}
                dev_corrs = {}
                dev_corrs_ew = {}
                for other_id in other_ids:
                    pair = [p for p in pairs if market_id in p.split('_') and other_id in p.split('_')][0]
                    corr, corr_index = market_correlation[pair]
                    move_corrs[other_id] = corr[corr_index[date]][MOVEMENT_CORR] if date in corr_index \
                        else (json.loads(values[-1][6])[other_id] if len(values) and int(market_id) == values[-1][0] else 0.0)
                    move_corrs_ew[other_id] = corr[corr_index[date]][MOVEMENT_CORR_EW] if date in corr_index \
                        else (json.loads(values[-1][7])[other_id] if len(values) and int(market_id) == values[-1][0] else 0.0)
                    dev_corrs[other_id] = corr[corr_index[date]][DEVIATION_CORR] if date in corr_index \
                        else (json.loads(values[-1][8])[other_id] if len(values) and int(market_id) == values[-1][0] else 0.0)
                    dev_corrs_ew[other_id] = corr[corr_index[date]][DEVIATION_CORR_EW] if date in corr_index \
                        else (json.loads(values[-1][9])[other_id] if len(values) and int(market_id) == values[-1][0] else 0.0)

                values.append((
                    int(market_id),
                    market_code,
                    lookback,
                    date,
                    v[MOVEMENT_VOL],
                    v[DEVIATION_VOL],
                    json.dumps(move_corrs),
                    json.dumps(move_corrs_ew),
                    json.dumps(dev_corrs),
                    json.dumps(dev_corrs_ew)
                ))

    return values


def aggregate_group_values(group_ids, lookback, investment_universe_name):
    """
    Aggregate volatility, correlation and other values for inserting to the DB
    
    :param group_ids:                   list of group IDs
    :param lookback:                    lookback window used for calculating the values
    :param investment_universe_name:    name of the investment universe
    :return:                            list of tuples(group_id, lookback, date, move_vol, dev_vol, move_corr, dev_corr)
    """
    msg = 'Aggregating group values'
    length = float(len(group_ids))

    RETURN = 1
    MOVEMENT_VOL = 3
    DEVIATION_VOL = 4
    MOVEMENT_CORR = 1
    DEVIATION_CORR = 2
    MOVEMENT_CORR_EW = 3
    DEVIATION_CORR_EW = 4
    values = []
    corr_keys = group_correlation.keys()
    for i, group_id in enumerate(group_ids):
        log(msg, group_id, i, length)

        pairs = [k for k in corr_keys if group_id in k.split('_')]
        other_ids = filter(lambda i: i != group_id, reduce(lambda r, p: r + p.split('_'), pairs, []))
        for date in sorted(group_volatility_indexes):
            i = group_volatility_indexes[date]
            rets = group_volatility[i][RETURN]
            move_vols = group_volatility[i][MOVEMENT_VOL]
            dev_vols = group_volatility[i][DEVIATION_VOL]
            if len(move_vols) and len(dev_vols):
                ret = rets[group_id] if group_id in rets else (values[-1][3] if len(values) else 0.0)
                move_vol = move_vols[group_id] if group_id in move_vols else (values[-1][4] if len(values) else 0.0)
                dev_vol = dev_vols[group_id] if group_id in dev_vols else (values[-1][5] if len(values) else 0.0)
                move_corrs = {}
                move_corrs_ew = {}
                dev_corrs = {}
                dev_corrs_ew = {}
                for other_id in other_ids:
                    pair = [p for p in pairs if group_id in p.split('_') and other_id in p.split('_')][0]
                    corr, corr_indexes = group_correlation[pair]
                    move_corrs[other_id] = corr[corr_indexes[date]][MOVEMENT_CORR] if date in corr_indexes \
                        else (json.loads(values[-1][7])[other_id] if len(values) and int(group_id) == values[-1][0] else 0.0)
                    move_corrs_ew[other_id] = corr[corr_indexes[date]][MOVEMENT_CORR_EW] if date in corr_indexes \
                        else (json.loads(values[-1][8])[other_id] if len(values) and int(group_id) == values[-1][0] else 0.0)
                    dev_corrs[other_id] = corr[corr_indexes[date]][DEVIATION_CORR] if date in corr_indexes \
                        else (json.loads(values[-1][9])[other_id] if len(values) and int(group_id) == values[-1][0] else 0.0)
                    dev_corrs_ew[other_id] = corr[corr_indexes[date]][DEVIATION_CORR_EW] if date in corr_indexes \
                        else (json.loads(values[-1][10])[other_id] if len(values) and int(group_id) == values[-1][0] else 0.0)

                values.append((
                    int(group_id),
                    lookback,
                    investment_universe_name,
                    date,
                    ret,
                    move_vol,
                    dev_vol,
                    json.dumps(move_corrs),
                    json.dumps(move_corrs_ew),
                    json.dumps(dev_corrs),
                    json.dumps(dev_corrs_ew)
                ))

    return values


def delete_values(table, lookback):
    connection.cursor().execute('DELETE FROM `%s` WHERE lookback = %s' % (table, lookback))


def insert_market_values(values):
    columns = [
        'market_id',
        'market_code',
        'lookback',
        'date',
        'movement_volatility',
        'dev_volatility',
        'movement_correlations',
        'movement_correlations_ew',
        'dev_correlations',
        'dev_correlations_ew'
    ]
    insert_values('market_correlation', columns, values)


def insert_group_values(values):
    columns = [
        'group_id',
        'lookback',
        'investment_universe_name',
        'date',
        'returns',
        'movement_volatility',
        'dev_volatility',
        'movement_correlations',
        'movement_correlations_ew',
        'dev_correlations',
        'dev_correlations_ew'
    ]
    insert_values('group_correlation', columns, values)


def insert_values(table, columns, values):
    command = 'INSERT INTO `%s` (%s) VALUES(%s)' % (table, ', '.join(columns), ('%s, ' * len(columns))[:-2])

    with connection:
        cursor = connection.cursor()
        cursor.executemany(command, values)


def calculate_markets(market_ids, start_date, end_date, lookback, persist=False):
    market_id_pairs = [c for c in combinations(map(str, market_ids), 2)]
    market_codes = {market_id: __market_code(market_id) for market_id in market_ids}

    msg = 'Calculating volatility'
    length = float(len(market_ids))
    map(lambda i: log(msg, i[1], i[0], length)
                  and calculate_volatility(i[1], market_codes[i[1]], start_date, end_date, lookback), enumerate(market_ids))

    msg = 'Calculating correlation'
    length = float(len(market_id_pairs))
    map(lambda i: log(msg, i[1], i[0], length)
                  and calculate_correlation(i[1][0], i[1][1], lookback), enumerate(market_id_pairs))
    log(msg, index=int(length), length=length, complete=True)

    if persist:
        msg = 'Aggregating market values'
        market_values = aggregate_market_values(market_ids, market_codes, lookback)
        log(msg, index=len(market_ids), length=float(len(market_ids)), complete=True)

        msg = 'Inserting market values'
        length = float(len(market_values))
        block = int(length / 10)
        print 'Deleting market values with lookback', lookback
        delete_values('market_correlation', lookback)
        for i in range(10 + 1):
            log(msg, '', i, 10.0)
            insert_market_values(market_values[i*block:(i+1)*block])
        log(msg, index=10, length=10.0, complete=True)


def calculate_groups(market_ids, investment_universe_name, lookback, persist=False):
    groups = {market_id: str(__group_id(market_id)[0]) for market_id in market_ids}
    group_ids = set([groups[k] for k in groups.keys()])
    group_id_pairs = [c for c in combinations(map(str, group_ids), 2)]

    calculate_group_volatility(market_ids, groups, lookback)
    clean_group_volatility(groups)

    msg = 'Calculating group correlation'
    length = float(len(group_id_pairs))
    map(lambda i: log(msg, i[1], i[0], length)
                  and calculate_group_correlation(i[1][0], i[1][1], lookback), enumerate(group_id_pairs))
    log(msg, index=int(length), length=length, complete=True)

    if persist:
        msg = 'Aggregating group values'
        group_values = aggregate_group_values(group_ids, lookback, investment_universe_name)
        log(msg, index=len(group_ids), length=float(len(group_ids)), complete=True)

        msg = 'Inserting group values'
        length = float(len(group_values))
        block = int(length / 10)
        print 'Deleting group values with lookback', lookback
        delete_values('group_correlation', lookback)
        for i in range(10 + 1):
            log(msg, '', i, 10.0)
            insert_group_values(group_values[i*block:(i+1)*block])
        log(msg, index=10, length=10.0, complete=True)


def main(lookback, investment_universe_name, persist_market_values=True, persist_group_values=True):
    start = time.time()
    investment_universe = __investment_universe(investment_universe_name)
    start_date = dt.date(1979, 1, 1)
    # start_date = dt.date(1991, 1, 1)
    end_date = dt.date(2017, 12, 31)
    # end_date = dt.date(1992, 12, 31)
    market_ids = investment_universe[2].split(',')
    # market_ids = ['55','79']

    calculate_markets(market_ids, start_date, end_date, lookback, persist=persist_market_values)
    calculate_groups(market_ids, investment_universe_name, lookback, persist=persist_group_values)

    print 'Time:', time.time() - start, (time.time() - start) / 60


if __name__ == '__main__':
    main(25, '25Y', persist_market_values=True, persist_group_values=True)
