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
from itertools import chain
from operator import itemgetter
from collections import defaultdict
from collections import deque

connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)
market_correlation_data = {}
group_correlation_data = {}


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


def fetch_market_correlation_data(market_ids, lookback):
    market_correlation_query = """
        SELECT 
            date, 
            movement_correlations, 
            movement_correlations_ew, 
            dev_correlations, 
            dev_correlations_ew
        FROM market_correlation 
        WHERE lookback = '%s' AND market_id = '%s'
        ORDER BY date;
    """

    msg = 'Fetching market correlations'
    length = float(len(market_ids))
    cursor = connection.cursor()
    for i, market_id in enumerate(market_ids):
        log(msg, market_id, i, length)
        cursor.execute(market_correlation_query % (lookback, market_id))
        market_correlation_data[market_id] = cursor.fetchall()

    log(msg, index=int(length), length=length, complete=True)


def fetch_group_correlation_data(group_ids, lookback):
    group_correlation_query = """
        SELECT 
            date, 
            movement_correlations, 
            movement_correlations_ew, 
            dev_correlations, 
            dev_correlations_ew
        FROM group_correlation 
        WHERE lookback = '%s' AND group_id = '%s'
        ORDER BY date;
    """

    msg = 'Fetching group correlations'
    length = float(len(group_ids))
    cursor = connection.cursor()
    for i, group_id in enumerate(group_ids):
        log(msg, group_id, i, length)
        cursor.execute(group_correlation_query % (lookback, group_id))
        group_correlation_data[group_id] = cursor.fetchall()

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

    MOVEMENT_CORR = 1
    MOVEMENT_CORR_EW = 2
    DEV_CORR = 3
    DEV_CORR_EW = 3

    result = []
    dates = reduce(lambda r, market_id: r + [d[0] for d in market_correlation_data[market_id]], market_ids, [])
    # for date in sorted(set(dates)):

    # market correlations
    data = defaultdict(dict)
    for market_id in market_ids:
        index = market_id_idx[market_id]

        corrs = json.loads(market_correlation_data[market_id][-1][MOVEMENT_CORR])
        keys = [k for k in map(int, corrs.keys()) if k in market_ids]
        data[market_id]['movement_correlations'] = [[index, market_id_idx[k], corrs[str(k)]] for k in keys] + [[index, index, 1.0]]

        corrs = json.loads(market_correlation_data[market_id][-1][MOVEMENT_CORR_EW])
        keys = [k for k in map(int, corrs.keys()) if k in market_ids]
        data[market_id]['movement_correlations_ew'] = [[index, market_id_idx[k], corrs[str(k)]] for k in keys] + [[index, index, 1.0]]

        corrs = json.loads(market_correlation_data[market_id][-1][DEV_CORR])
        keys = [k for k in map(int, corrs.keys()) if k in market_ids]
        data[market_id]['dev_correlations'] = [[index, market_id_idx[k], corrs[str(k)]] for k in keys] + [[index, index, 1.0]]

        corrs = json.loads(market_correlation_data[market_id][-1][DEV_CORR_EW])
        keys = [k for k in map(int, corrs.keys()) if k in market_ids]
        data[market_id]['dev_correlations_ew'] = [[index, market_id_idx[k], corrs[str(k)]] for k in keys] + [[index, index, 1.0]]

    # group correlations
    group_correlations = defaultdict(dict)
    for group_id in group_ids:
        corrs = json.loads(group_correlation_data[group_id][-1][MOVEMENT_CORR])
        group_correlations[group_id]['movement_correlations'] = {k: corrs[k] for k in corrs.keys() if int(k) in group_ids}

        corrs = json.loads(group_correlation_data[group_id][-1][MOVEMENT_CORR_EW])
        group_correlations[group_id]['movement_correlations_ew'] = {k: corrs[k] for k in corrs.keys() if int(k) in group_ids}

        corrs = json.loads(group_correlation_data[group_id][-1][DEV_CORR])
        group_correlations[group_id]['dev_correlations'] = {k: corrs[k] for k in corrs.keys() if int(k) in group_ids}

        corrs = json.loads(group_correlation_data[group_id][-1][DEV_CORR_EW])
        group_correlations[group_id]['dev_correlations_ew'] = {k: corrs[k] for k in corrs.keys() if int(k) in group_ids}

    result.append((
        investment_universe_name,
        dt.date(2017, 8, 10),
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
    # start_date = dt.date(1979, 1, 1)
    start_date = dt.date(1991, 1, 1)
    # end_date = dt.date(2017, 12, 31)
    end_date = dt.date(1992, 12, 31)
    # market_ids = __market_ids(investment_universe_name)
    market_ids = [18, 19, 24, 25, 27]  # "OJ","SB","C","KW","MW"
    market_data = __market_data()
    groups = {m[0]: m[3] for m in market_data if m[0] in market_ids}
    group_ids = set(groups.values())

    fetch_market_correlation_data(market_ids, lookback)
    fetch_group_correlation_data(group_ids, lookback)
    values = aggregated_values(investment_universe_name, lookback, market_ids, market_data, groups, group_ids)

    print 'Deleting values'
    delete_values(investment_universe_name, lookback)
    print 'Inserting values'
    insert_values(values)

    # msg = 'Inserting market values'
    # length = float(len(market_values))
    # block = int(length / 10)
    # print 'Deleting market values with lookback', lookback
    # delete_values('market_correlation', lookback)
    # for i in range(10 + 1):
    #     log(msg, '', i, 10.0)
    #     insert_market_values(market_values[i*block:(i+1)*block])
    # log(msg, index=10, length=10.0, complete=True)

    print 'Time:', time.time() - start, (time.time() - start) / 60


if __name__ == '__main__':
    if len(sys.argv) == 3 and len(sys.argv[1]) and len(sys.argv[2]):
        main(sys.argv[1], sys.argv[2])
    else:
        print 'Expected two arguments -- name of the investment universe and lookback period'

# correlations
# [
#     [0,2,0.07927669918845122],
#     [0,3,0.32015183468943853],
#     [0,4,-0.17574390685007296],
#     [0,1,0.29177873952605005],
#     [0,0,1.0],
#
#     [1,2,0.044201505646149004],
#     [1,3,-0.00044234233449471754],
#     [1,4,-0.43119303661405783],
#     [1,0,0.29177873952605005],
#     [1,1,1.0],
#
#     [2,3,0.6924798505088627],
#     [2,4,0.7053141002145532],
#     [2,1,0.044201505646149004],
#     [2,0,0.07927669918845122],
#     [2,2,1.0],
#
#     [3,2,0.6924798505088627],
#     [3,4,0.6121392646679655],
#     [3,1,-0.00044234233449471754],
#     [3,0,0.32015183468943853],
#     [3,3,1.0],
#
#     [4,2,0.7053141002145532],
#     [4,3,0.6121392646679655],
#     [4,1,-0.43119303661405783],
#     [4,0,-0.17574390685007296],
#     [4,4,1.0]
# ]

# group_correlations
# {"2":{"3":-0.02961567104489264},"3":{"2":-0.02961567104489264}}
