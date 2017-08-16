#!/usr/bin/python

import os
import sys
import time
import json
import datetime as dt
import MySQLdb as mysql
from itertools import groupby
from itertools import chain
from operator import itemgetter
from collections import defaultdict

connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)
market_correlation_data = {}
market_correlation_indexes = {}
group_correlation_data = {}
group_correlation_indexes = {}


def log(message, code='', index=0, length=0.0, complete=False):
    sys.stdout.write('%s\r' % (' ' * 80))
    if complete:
        sys.stdout.write('%s complete\r\n' % message)
    else:
        sys.stdout.write('%s %s (%d of %d) [%d %%]\r' % (message, code, index, length, index / length * 100))
    sys.stdout.flush()
    return True


def __market_ids(investment_universe_name):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT market_ids
        FROM investment_universe
        WHERE name = '%s';
    """ % investment_universe_name)
    return sorted(map(int, cursor.fetchone()[0].split(',')))


def __market_data():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            m.id, 
            m.name, 
            m.code, 
            m.group_id, 
            g.name 
        FROM market AS m INNER JOIN `group` AS g ON m.group_id = g.id
        """)
    return cursor.fetchall()


def fetch_market_correlation_data(market_ids, lookback, start_date, end_date):
    market_correlation_query = """
        SELECT 
            date, 
            movement_correlations, 
            movement_correlations_ew, 
            dev_correlations, 
            dev_correlations_ew
        FROM market_correlation 
        WHERE lookback = '%s' 
        AND market_id = '%s' 
        AND DATE(date) >= '%s' 
        AND DATE(date) <= '%s' 
        ORDER BY date;
    """

    msg = 'Fetching market correlations'
    length = float(len(market_ids))
    cursor = connection.cursor()
    for i, market_id in enumerate(market_ids):
        log(msg, market_id, i, length)
        cursor.execute(market_correlation_query % (lookback, market_id, start_date, end_date))
        market_correlation_data[market_id] = cursor.fetchall()
        market_correlation_indexes[market_id] = {i[1][0]: i[0] for i in enumerate(market_correlation_data[market_id])}

    log(msg, index=int(length), length=length, complete=True)


def fetch_group_correlation_data(group_ids, lookback, start_date, end_date):
    group_correlation_query = """
        SELECT 
            date, 
            movement_correlations, 
            movement_correlations_ew, 
            dev_correlations, 
            dev_correlations_ew
        FROM group_correlation 
        WHERE lookback = '%s' 
        AND group_id = '%s' 
        AND DATE(date) >= '%s' 
        AND DATE(date) <= '%s' 
        ORDER BY date;
    """

    msg = 'Fetching group correlations'
    length = float(len(group_ids))
    cursor = connection.cursor()
    for i, group_id in enumerate(group_ids):
        log(msg, group_id, i, length)
        cursor.execute(group_correlation_query % (lookback, group_id, start_date, end_date))
        group_correlation_data[group_id] = cursor.fetchall()
        group_correlation_indexes[group_id] = {i[1][0]: i[0] for i in enumerate(group_correlation_data[group_id])}

    log(msg, index=int(length), length=length, complete=True)


def delete_values(investment_universe_name, lookback):
    connection.cursor().execute("""
        DELETE FROM `correlation_matrix` 
        WHERE `investment_universe_name` = '%s' AND `lookback` = %s
    """ % (investment_universe_name, lookback))


def insert_values(values):
    columns = [
        'investment_universe_name',
        'date',
        'lookback',
        'categories',
        'movement_market_correlations',
        'movement_market_correlations_ew',
        'movement_group_correlations',
        'movement_group_correlations_ew',
        'dev_market_correlations',
        'dev_market_correlations_ew',
        'dev_group_correlations',
        'dev_group_correlations_ew'
    ]
    command = 'INSERT INTO correlation_matrix (%s) VALUES(%s)' % (', '.join(columns), ('%s, ' * len(columns))[:-2])

    with connection:
        cursor = connection.cursor()
        cursor.executemany(command, values)


def aggregated_values(investment_universe_name, lookback, market_ids, market_data, groups, group_ids):
    market_codes = {m[0]: m[2] for m in market_data}
    grouped_market_ids = {i[0]: map(lambda l: l[0], i[1]) for i in groupby(sorted(groups.items(), key=itemgetter(1)), key=itemgetter(1))}
    flat_market_ids = [item for sublist in [grouped_market_ids[k] for k in grouped_market_ids.keys()] for item in sublist]
    market_id_idx = {k: i for i, k in enumerate(flat_market_ids)}

    precision = 4
    DATE = 0
    MOVEMENT_CORR = 1
    MOVEMENT_CORR_EW = 2
    DEV_CORR = 3
    DEV_CORR_EW = 3

    result = []
    dates = reduce(lambda r, market_id: r + [d[0] for d in market_correlation_data[market_id]], market_ids, [])
    for date in sorted(set(dates)):
        # market correlations
        data = defaultdict(dict)
        for market_id in market_ids:
            index = market_id_idx[market_id]
            corr_data = market_correlation_data[market_id][market_correlation_indexes[market_id][date]] \
                if date in market_correlation_indexes[market_id] else [d for d in market_correlation_data[market_id] if d[0] <= date]

            if len(corr_data):
                corr_data = corr_data if type(corr_data[DATE]) is dt.date else corr_data[-1]

                corrs = json.loads(corr_data[MOVEMENT_CORR])
                keys = [k for k in map(int, corrs.keys()) if k in market_ids]
                data[market_id]['movement_correlations'] = [[index, market_id_idx[k], round(corrs[str(k)], precision)]
                                                            for k in keys] + [[index, index, 1.0]]

                corrs = json.loads(corr_data[MOVEMENT_CORR_EW])
                keys = [k for k in map(int, corrs.keys()) if k in market_ids]
                data[market_id]['movement_correlations_ew'] = [[index, market_id_idx[k], round(corrs[str(k)], precision)]
                                                               for k in keys] + [[index, index, 1.0]]

                corrs = json.loads(corr_data[DEV_CORR])
                keys = [k for k in map(int, corrs.keys()) if k in market_ids]
                data[market_id]['dev_correlations'] = [[index, market_id_idx[k], round(corrs[str(k)], precision)]
                                                       for k in keys] + [[index, index, 1.0]]

                corrs = json.loads(corr_data[DEV_CORR_EW])
                keys = [k for k in map(int, corrs.keys()) if k in market_ids]
                data[market_id]['dev_correlations_ew'] = [[index, market_id_idx[k], round(corrs[str(k)], precision)]
                                                          for k in keys] + [[index, index, 1.0]]
            else:
                keys = [k for k in market_ids if k != market_id]
                corr_data = [[index, market_id_idx[k], 1.0] for k in keys] + [[index, index, 1.0]]
                data[market_id]['movement_correlations'] = corr_data
                data[market_id]['movement_correlations_ew'] = corr_data
                data[market_id]['dev_correlations'] = corr_data
                data[market_id]['dev_correlations_ew'] = corr_data

        # group correlations
        group_correlations = defaultdict(dict)
        for group_id in group_ids:
            corr_data = group_correlation_data[group_id][group_correlation_indexes[group_id][date]] \
                if date in group_correlation_indexes[group_id] else [d for d in group_correlation_indexes[group_id] if d[0] <= date]

            if len(corr_data):
                corr_data = corr_data if type(corr_data[DATE]) is dt.date else corr_data[-1]

                corrs = json.loads(corr_data[MOVEMENT_CORR])
                group_correlations[group_id]['movement_correlations'] = {k: round(corrs[k], precision)
                                                                         for k in corrs.keys() if int(k) in group_ids}

                corrs = json.loads(corr_data[MOVEMENT_CORR_EW])
                group_correlations[group_id]['movement_correlations_ew'] = {k: round(corrs[k], precision)
                                                                            for k in corrs.keys() if int(k) in group_ids}

                corrs = json.loads(corr_data[DEV_CORR])
                group_correlations[group_id]['dev_correlations'] = {k: round(corrs[k], precision)
                                                                    for k in corrs.keys() if int(k) in group_ids}

                corrs = json.loads(corr_data[DEV_CORR_EW])
                group_correlations[group_id]['dev_correlations_ew'] = {k: round(corrs[k], precision)
                                                                       for k in corrs.keys() if int(k) in group_ids}
            else:
                keys = [k for k in group_id if k != group_ids]
                corr_data = {k: 1.0 for k in keys}
                group_correlations[group_id]['movement_correlations'] = corr_data
                group_correlations[group_id]['movement_correlations_ew'] = corr_data
                group_correlations[group_id]['dev_correlations'] = corr_data
                group_correlations[group_id]['dev_correlations_ew'] = corr_data

        result.append((
            investment_universe_name,
            date,
            lookback,
            json.dumps([market_codes[market_id] for market_id in market_ids]),
            json.dumps(list(chain(*[data[market_id]['movement_correlations'] for market_id in market_ids]))),
            json.dumps(list(chain(*[data[market_id]['movement_correlations_ew'] for market_id in market_ids]))),
            json.dumps({group_id: group_correlations[group_id]['movement_correlations'] for group_id in group_ids}),
            json.dumps({group_id: group_correlations[group_id]['movement_correlations_ew'] for group_id in group_ids}),
            json.dumps(list(chain(*[data[market_id]['dev_correlations'] for market_id in market_ids]))),
            json.dumps(list(chain(*[data[market_id]['dev_correlations_ew'] for market_id in market_ids]))),
            json.dumps({group_id: group_correlations[group_id]['dev_correlations'] for group_id in group_ids}),
            json.dumps({group_id: group_correlations[group_id]['dev_correlations_ew'] for group_id in group_ids})
        ))

    return result


def main(investment_universe_name, lookback):
    start = time.time()
    start_date = dt.date(1979, 1, 1).strftime('%Y-%m-%d')
    # start_date = dt.date(2017, 6, 1).strftime('%Y-%m-%d')
    end_date = dt.date(2017, 12, 31).strftime('%Y-%m-%d')
    # end_date = dt.date(2017, 6, 9).strftime('%Y-%m-%d')
    market_ids = __market_ids(investment_universe_name)
    # market_ids = [18, 19, 24, 25, 27]  # "OJ","SB","C","KW","MW"
    market_data = __market_data()
    groups = {m[0]: m[3] for m in market_data if m[0] in market_ids}
    group_ids = set(groups.values())

    fetch_market_correlation_data(market_ids, lookback, start_date, end_date)
    fetch_group_correlation_data(group_ids, lookback, start_date, end_date)
    values = aggregated_values(investment_universe_name, lookback, market_ids, market_data, groups, group_ids)

    print 'Deleting values'
    delete_values(investment_universe_name, lookback)
    print 'Inserting values'
    insert_values(values)

    print 'Time:', time.time() - start, (time.time() - start) / 60


if __name__ == '__main__':
    if len(sys.argv) == 3 and len(sys.argv[1]) and len(sys.argv[2]):
        main(sys.argv[1], sys.argv[2])
    else:
        print 'Expected two arguments -- name of the investment universe and lookback period'
