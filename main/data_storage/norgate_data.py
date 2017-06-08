#!/usr/bin/env python

import os
import re
import csv
import sys
import json
import calendar
import datetime as dt
import MySQLdb as mysql
from collections import defaultdict

norgate_dir_template = './data/norgate/%s.csv'
mysql_connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)


def out(message):
    print message
    return True


def csv_lines(path, exclude_header=True, filter_index=0):
    reader = csv.reader(open(path), delimiter=',', quotechar='"')
    rows = [row for row in reader if re.match('^[a-zA-Z0-9]', row[filter_index])]
    return rows[1:] if exclude_header else rows


def query(table, columns, placeholders):
    return 'INSERT INTO `%s` (%s) VALUES (%s)' % (table, columns, placeholders)


def insert_values(operation, values):
    with mysql_connection:
        cursor = mysql_connection.cursor()
        cursor.executemany(operation, values)


def populate_exchange_table(schema):
    code = 0
    ex_code = 1
    name = 2
    country = 4
    insert_values(
        query(schema, 'code, ex_code, name, country', "%s, %s, %s, %s"),
        [(l[code], l[ex_code], l[name], l[country]) for l in csv_lines(norgate_dir_template % schema)]
    )


def populate_delivery_month_table(schema):
    insert_values(
        query(schema, 'code, name, short_name', "%s, %s, %s"),
        csv_lines(norgate_dir_template % schema)
    )


def populate_data_codes_table(schema):
    insert_values(
        query(schema, 'code, appendix, name', "%s, %s, %s"),
        csv_lines(norgate_dir_template % schema)
    )


def populate_group_table(schema):
    insert_values(
        query(schema, 'name, standard', "%s, %s"),
        csv_lines(norgate_dir_template % schema)
    )


def populate_market(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT name, id FROM `group` WHERE standard='Norgate'")
    groups = dict(cursor.fetchall())
    cursor.execute("SELECT name, id FROM `exchange`")
    exchanges = dict(cursor.fetchall())
    columns = {
        'name': 0,
        'code': 4,
        'data_codes': 5,
        'exchange_id': 6,
        'group_id': 8,
        'contract_size': 9,
        'quotation': 10,
        'tick_size': 11,
        'tick_value': 12,
        'point_value': 13,
        'currency': 14,
        'first_contract': 15,
        'first_data_date': 16,
        'volume_offset': 17,
        'oi_offset': 18,
        'last_trading_day': 19,
        'first_notice_day': 20,
        'intraday_initial_margin': 21,
        'intraday_maintenance_margin': 22,
        'overnight_initial_margin': 23,
        'overnight_maintenance_margin': 24
    }
    IB_columns = {
        'underlying': 2,
        'trading_class': 3,
        'exchange_code': 7
    }
    keys = columns.keys()
    markets = csv_lines(norgate_dir_template % schema)
    IB_margins = csv_lines(norgate_dir_template % 'IB_margins')

    # TODO move following 'utility' functions to its own library
    def contains(key, data, market): return market[columns.get(key)] in data

    def print_lookup_error(m, key):
        print "[ERROR] Can't find '%s'. Skipping inserting '%s'" % (m[columns.get(key)], m[columns.get('name')])

    def format_dates(m):
        d = m[columns.get('first_contract')].split('/')
        m[columns.get('first_contract')] = dt.date(int(d[2]), int(d[0]), 1)
        d = m[columns.get('first_data_date')].split('/')
        m[columns.get('first_data_date')] = dt.date(int(d[2]), int(d[0]), int(d[1]))
        return True

    def replace_ids(m):
        m[columns.get('exchange_id')] = exchanges.get(m[columns.get('exchange_id')])
        m[columns.get('group_id')] = groups.get(m[columns.get('group_id')])
        return True

    # TODO also include in the 'map'?
    def append_margins(m):
        margins = [[g[5], g[6], g[7], g[8]] for g in IB_margins  # TODO remove hard-coded indexes
                    if g[1] == m[IB_columns.get('exchange_code')]
                    and g[2] == m[IB_columns.get('underlying')]
                    and g[4] == m[IB_columns.get('trading_class')]]
        return m + map(lambda g: g if g != 'N/A' else 0, margins[0] if len(margins) else [0, 0, 0, 0])  # TODO simplify

    map(lambda m: (
        (contains('exchange_id', exchanges, m) or print_lookup_error(m, 'exchange_id'))
        and (contains('group_id', groups, m) or print_lookup_error(m, 'group_id'))
        and replace_ids(m)
        and format_dates(m)
    ), markets)

    insert_values(
        query(schema, ','.join(keys), ("%s, " * len(keys))[:-2]),
        [[append_margins(m)[columns.get(k)] for k in keys] for m in markets]
    )


def populate_spot_market(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT name, id FROM `group` WHERE standard='Spot'")
    groups = dict(cursor.fetchall())
    columns = {
        'name': 0,
        'code': 1,
        'group_id': 2,
        'first_data_date': 3,
        'notes': 4
    }
    keys = columns.keys()
    markets = csv_lines(norgate_dir_template % schema)

    # TODO move following 'utility' functions to its own library
    def contains(key, data, market): return market[columns.get(key)] in data

    def print_lookup_error(m, key):
        print "[ERROR] Can't find '%s'. Skipping inserting '%s'" % (m[columns.get(key)], m[columns.get('name')])

    def format_dates(m):
        d = m[columns.get('first_data_date')].split('/')
        m[columns.get('first_data_date')] = dt.date(int(d[2]), int(d[0]), int(d[1]))
        return True

    def replace_ids(m):
        m[columns.get('group_id')] = groups.get(m[columns.get('group_id')])
        return True

    map(lambda m: (
        (contains('group_id', groups, m) or print_lookup_error(m, 'group_id'))
        and replace_ids(m)
        and format_dates(m)
    ), markets)

    insert_values(
        query(schema, ','.join(keys), ("%s, " * len(keys))[:-2]),
        [[m[columns.get(k)] for k in keys] for m in markets]
    )


def populate_currencies(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT name, id FROM `group` WHERE standard='Currency'")
    groups = dict(cursor.fetchall())
    columns = {
        'code': 0,
        'name': 1,
        'group_id': 2
    }
    keys = columns.keys()
    markets = csv_lines(norgate_dir_template % schema)

    def contains(key, data, market): return market[columns.get(key)] in data

    def print_lookup_error(m, key):
        print "[ERROR] Can't find '%s'. Skipping inserting '%s'" % (m[columns.get(key)], m[columns.get('name')])

    def replace_ids(m):
        m[columns.get('group_id')] = groups.get(m[columns.get('group_id')])
        return True

    map(lambda m: (
        (contains('group_id', groups, m) or print_lookup_error(m, 'group_id'))
        and replace_ids(m)
    ), markets)

    insert_values(
        query(schema, ','.join(keys), ("%s, " * len(keys))[:-2]),
        [[m[columns.get(k)] for k in keys] for m in markets]
    )


def populate_currency_pairs(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT name, id FROM `group` WHERE standard='Currency'")
    groups = dict(cursor.fetchall())
    columns = {
        'name': 0,
        'code': 1,
        'group_id': 2,
        'first_data_date': 3  # TODO calculate from actual data
    }
    keys = columns.keys()
    pairs = csv_lines(norgate_dir_template % schema)

    # TODO move following 'utility' functions to its own library
    def contains(key, data, market): return market[columns.get(key)] in data

    def print_lookup_error(p, key):
        print "[ERROR] Can't find '%s'. Skipping inserting '%s'" % (p[columns.get(key)], p[columns.get('name')])

    # TODO use native formatting functionality
    def format_dates(p):
        d = p[columns.get('first_data_date')].split('/')
        p[columns.get('first_data_date')] = dt.date(int(d[2]), int(d[0]), int(d[1]))
        return True

    def replace_ids(p):
        p[columns.get('group_id')] = groups.get(p[columns.get('group_id')])
        return True

    map(lambda p: (
        (contains('group_id', groups, p) or print_lookup_error(p, 'group_id'))
        and replace_ids(p)
        and format_dates(p)
    ), pairs)

    insert_values(
        query(schema, ','.join(keys), ("%s, " * len(keys))[:-2]),
        [[p[columns.get(k)] for k in keys] for p in pairs]
    )


def populate_contracts(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT code, appendix FROM `data_codes`")
    data_codes = dict(cursor.fetchall())
    cursor.execute("SELECT id, code, data_codes FROM `market`")
    codes = cursor.fetchall()
    cursor.execute("SELECT code, name FROM `delivery_month`")
    delivery_months = cursor.fetchall()
    dir_path = './resources/Norgate/data/Futures/Contracts/_Text/'
    dir_list = os.listdir(dir_path)
    now = dt.datetime.now()
    all_codes = reduce(lambda result, c: result + map(lambda d: (c[0], c[1] + data_codes[d]), c[2]), codes, [])
    matching_codes = filter(lambda c: c[1] in dir_list, all_codes)
    # TODO use 'Entity' that will hold the structure description and generalize the SQL insertion
    columns = [
        'market_id',
        'expiration_date',
        'code',
        'price_date',
        'open_price',
        'high_price',
        'low_price',
        'last_price',
        'settle_price',
        'volume',
        'open_interest',
        'last_trading_day',
        'created_date',
        'last_updated_date'
    ]
    q = query(schema, ','.join(columns), ("%s, " * len(columns))[:-2])

    for code in matching_codes:
        populate_symbol(now, code, dir_path, delivery_months, q)


def populate_symbol(now, code, dir_path, delivery_months, q):
    files = os.listdir(''.join([dir_path, code[1]]))
    file_path = ''.join([dir_path, code[1], '/%s'])
    deliveries = defaultdict(list)

    def date(d):
        return dt.date(int(d[:4]), int(d[4:6]), int(d[6:]))

    def index(key, data, position=0):
        return reduce(lambda i, d: i + 1 if d[position] <= key else i, data, 0)

    def values(file_name):
        delivery = file_name[5:10]
        expiration_date = dt.date(int(delivery[:-1]), index(delivery[-1], delivery_months), 1)
        rows = csv_lines(file_path % file_name, exclude_header=False)
        last_date = date(rows[-1][0])
        last_trading_date = last_date

        # TODO calculate actual expiration date properly
        if last_date < last_data_date:
            deliveries[delivery[-1]].append(last_date)
        else:
            delivery_dates = deliveries[delivery[-1]]
            month = max(delivery_dates).month if len(delivery_dates) else None
            year = int(delivery[:-1])
            dates = [d for d in deliveries[delivery[-1]] if d.month == month]
            day = int(round(sum([d.day for d in dates]) / len(dates))) if len(delivery_dates) else 1
            last_trading_date = dt.date(year, month, min(calendar.monthrange(year, month)[1], day)) if month else None

        return [[
             code[0],
             expiration_date,
             code[1] + delivery,
             r[0], r[1], r[2], r[3], r[4], r[4], r[5], r[6],
             last_trading_date,
             now,
             now
         ] for r in rows]

    last_data_date = date(csv_lines(file_path % sorted(files)[-1], exclude_header=False)[-1][0])

    map(lambda f: insert_values(q, values(f)), files)


def populate_continuous_adjusted(schema):
    populate_continuous(
        schema,
        './resources/Norgate/data/Futures/Continuous Contracts/Back Adjusted/Text/'
    )


def populate_continuous_spliced(schema):
    populate_continuous(
        schema,
        './resources/Norgate/data/Futures/Continuous Contracts/Spliced/Text/'
    )


def populate_continuous(schema, dir_path):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT code, appendix FROM `data_codes`")
    data_codes = dict(cursor.fetchall())
    cursor.execute("SELECT id, code, data_codes FROM `market`")
    codes = cursor.fetchall()
    cursor.execute("SELECT id, name FROM `roll_strategy` WHERE name = 'norgate'")
    roll_strategy_id = cursor.fetchone()[0]
    dir_list = [d.split('.')[0] for d in os.listdir(dir_path)]
    now = dt.datetime.now()
    all_codes = reduce(lambda result, c: result + map(lambda d: (c[0], c[1] + data_codes[d]), c[2]), codes, [])
    matching_codes = filter(lambda c: c[1] in dir_list, all_codes)
    columns = [
        'market_id',
        'roll_strategy_id',
        'code',
        'price_date',
        'open_price',
        'high_price',
        'low_price',
        'last_price',
        'settle_price',
        'volume',
        'open_interest',
        'created_date',
        'last_updated_date'
    ]
    q = query(schema, ','.join(columns), ("%s, " * len(columns))[:-2])

    def values(code):
        rows = csv_lines(''.join([dir_path, code[1], '.csv']), exclude_header=False)
        return [[code[0], roll_strategy_id, code[1], r[0], r[1], r[2], r[3], r[4], r[4], r[5], r[6], now, now] for r in rows]

    map(lambda c: insert_values(q, values(c)), matching_codes)


def populate_spot(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT id, code FROM `spot_market`")
    codes = cursor.fetchall()
    dir_path = './resources/Norgate/data/Futures/Cash/Text/'
    dir_list = [d.split('.')[0] for d in os.listdir(dir_path)]
    now = dt.datetime.now()
    matching_codes = filter(lambda c: c[1] in dir_list, codes)
    columns = [
        'spot_market_id',
        'price_date',
        'open_price',
        'high_price',
        'low_price',
        'last_price',
        'settle_price',
        'created_date',
        'last_updated_date'
    ]
    q = query(schema, ','.join(columns), ("%s, " * len(columns))[:-2])

    def values(code):
        rows = csv_lines(''.join([dir_path, code[1], '.csv']), exclude_header=False)
        return [[code[0], r[0], r[1], r[2], r[3], r[4], r[4], now, now] for r in rows]

    map(lambda c: insert_values(q, values(c)), matching_codes)


def populate_currency(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT id, code FROM `currency_pairs`")
    codes = cursor.fetchall()
    norgate_dir_path = './resources/Norgate/data/Forex/'
    ubc_dir_path = './resources/UBC/generated/full/'
    file_list = {
        'norgate': [d.split('.')[0] for d in os.listdir(norgate_dir_path)],
        'ubc': [d for d in os.listdir(ubc_dir_path)]
    }
    now = dt.datetime.now()
    matching_codes = filter(lambda c: c[1] in file_list['norgate'], codes)
    columns = [
        'currency_pair_id',
        'price_date',
        'open_price',
        'high_price',
        'low_price',
        'last_price',
        'created_date',
        'last_updated_date'
    ]
    q = query(schema, ','.join(columns), ("%s, " * len(columns))[:-2])

    def format_date(c):
        d = c.split('/')
        return dt.date(int(d[2]), int(d[0]), int(d[1]))

    def full_data(code, rows):
        ubc_file_name = [f for f in file_list['ubc'] if f.startswith(code)]
        ubc_rows = csv_lines(''.join([ubc_dir_path, ubc_file_name[0]])) if len(ubc_file_name) else []
        ubc_fill = [r for r in ubc_rows if format_date(r[0]) < format_date(rows[0][0])]
        return ubc_fill + rows if len(ubc_fill) else rows

    def values(code):
        rows = csv_lines(''.join([norgate_dir_path, code[1], '.csv']))
        return [[code[0], format_date(r[0]), r[1], r[2], r[3], r[4], now, now] for r in full_data(code[1], rows)]

    map(lambda c: insert_values(q, values(c)), matching_codes)


def populate_investment_universe(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT code, id FROM `market`")
    codes = dict(cursor.fetchall())
    lines = csv_lines('./data/%s.csv' % schema)
    columns = {
        'market_name': 0,
        'market_code': 1,
        'first_contract_date': 2,
        'first_data_date': 3,
        'currency': 4,
        'group': 5,
        'name': 6
    }

    def add(d, l):
        if len(l[columns.get('market_code')]) and len(l[columns.get('first_data_date')]):
            d[l[columns.get('name')]].append(str(codes[l[columns.get('market_code')]]))
        return d

    def dates(d, l, column):
        if len(l[columns.get(column)]):
            date_items = '{2}-{0}-{1}'.format(*l[columns.get(column)].split('/'))
            d[l[columns.get('name')]].append(dt.date(*map(int, date_items.split('-'))))
        return d

    universes = reduce(add, lines, defaultdict(list))
    contract_dates = reduce(lambda d, l: dates(d, l, 'first_contract_date'), lines, defaultdict(list))
    data_dates = reduce(lambda d, l: dates(d, l, 'first_data_date'), lines, defaultdict(list))

    if all([len(universes[k]) == len(set(universes[k])) for k in universes.keys()]):
        insert_values(
            query(schema, 'name, contract_start_date, data_start_date, market_ids', "%s, %s, %s, %s"),
            [[k, max(contract_dates[k]), max(data_dates[k]), ','.join(universes[k])] for k in universes.keys()]
        )
    else:
        print 'Not all markets in investment universe are unique'


def populate_standard_roll_schedule(schema):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT code, id FROM `market`")
    codes = cursor.fetchall()
    lines = csv_lines('./data/%s.csv' % schema, True, 2)
    columns = [
        'name',
        'market_id',
        'roll_out_month',
        'roll_in_month',
        'month',
        'day'
    ]

    values = []
    roll_out_month = 2
    roll_in_month = 3
    month = 4
    day = 5
    schedule_name = lines[0][0]
    code = lines[0][1]
    for l in lines:
        schedule_name = l[0] or schedule_name
        code = l[1] or code
        market_id = [c[1] for c in codes if c[0] == code][0]
        values.append((schedule_name, market_id, l[roll_out_month], l[roll_in_month], l[month], l[day]))

    insert_values(query(schema, ','.join(columns), ("%s, " * len(columns))[:-2]), values)


def populate_roll_strategy(schema):
    insert_values(
        query(schema, 'name, type, params', '%s, %s, %s'),
        [
            ('norgate', 'standard_roll', None),
            ('standard_roll_1', 'standard_roll', json.dumps({'schedule': 'norgate'}))
        ]
    )


if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        schema = sys.argv[1]
        schema_map = [
            ('exchange', populate_exchange_table),
            ('delivery_month', populate_delivery_month_table),
            ('data_codes', populate_data_codes_table),
            ('group', populate_group_table),
            ('market', populate_market),
            ('contract', populate_contracts),
            ('standard_roll_schedule', populate_standard_roll_schedule),
            ('roll_strategy', populate_roll_strategy),
            ('continuous_adjusted', populate_continuous_adjusted),
            ('continuous_spliced', populate_continuous_spliced),
            ('spot_market', populate_spot_market),
            ('spot', populate_spot),
            ('currencies', populate_currencies),
            ('currency_pairs', populate_currency_pairs),
            ('currency', populate_currency),
            ('investment_universe', populate_investment_universe)
        ]

        if schema == 'all':
            map(lambda s: (out("Populating %s" % s[0]) and s[1](s[0])), schema_map)
        elif any(item[0] == schema for item in schema_map):
            # TODO any native collection that would do this? If not, create one ...
            filter(lambda s: s[0] == schema, schema_map)[0][1](schema)
        else:
            print 'No schema of such name (%s) found.' % schema
            print 'Available schemas are: %s' % ', '.join([s[0] for s in schema_map])
            print 'OR passing in "all" to populate all available tables'
    else:
        print 'Expected one argument - name of the table to insert data into'
        print 'OR passing in "all" to populate all available tables'
