#!/usr/bin/env python

import os
import re
import csv
import sys
import datetime as dt
import MySQLdb as mysql

norgate_dir_template = './data/norgate/%s.csv'
mysql_connection = mysql.connect(
    os.environ['DB_HOST'],
    os.environ['DB_USER'],
    os.environ['DB_PASS'],
    os.environ['DB_NAME']
)


def csv_lines(path, exclude_header=True):
    reader = csv.reader(open(path), delimiter=',', quotechar='"')
    rows = [row for row in reader if re.match('^[a-zA-Z0-9]', row[0])]
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
        query(schema, 'code, name', "%s, %s"),
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
        'code': 2,
        'data_codes': 3,
        'exchange_id': 4,
        'group_id': 5,
        'contract_size': 6,
        'quotation': 7,
        'tick_size': 8,
        'tick_value': 9,
        'point_value': 10,
        'currency': 11,
        'first_contract': 12,
        'first_data_date': 13,
        'last_trading_day': 14,
        'first_notice_day': 15
    }
    keys = columns.keys()
    markets = csv_lines(norgate_dir_template % schema)

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

    map(lambda m: (
        (contains('exchange_id', exchanges, m) or print_lookup_error(m, 'exchange_id'))
        and (contains('group_id', groups, m) or print_lookup_error(m, 'group_id'))
        and replace_ids(m)
        and format_dates(m)
    ), markets)

    insert_values(
        query(schema, ','.join(keys), ("%s, " * len(keys))[:-2]),
        [[m[columns.get(k)] for k in keys] for m in markets]
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
        'delivery_date',
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
        'created_date',
        'last_updated_date'
    ]
    q = query(schema, ','.join(columns), ("%s, " * len(columns))[:-2])

    for code in matching_codes:
        populate_symbol(now, code, dir_path, delivery_months, q)


def populate_symbol(now, code, dir_path, delivery_months, q):
    files = os.listdir(''.join([dir_path, code[1]]))

    def index(key, data, position=0):
        return reduce(lambda i, d: i + 1 if d[position] <= key else i, data, 0)

    def values(file_name):
        delivery = file_name[5:10]
        delivery_date = dt.date(int(delivery[:-1]), index(delivery[-1], delivery_months), 1)
        rows = csv_lines(''.join([dir_path, code[1], '/', file_name]), exclude_header=False)
        return [[
             code[0],
             delivery_date,
             delivery_date,
             code[1] + delivery,
             r[0], r[1], r[2], r[3], r[4], r[4], r[5], r[6],
             now,
             now
         ] for r in rows]

    map(lambda f: insert_values(q, values(f)), files)


def populate_continuous_back_adjusted(schema):
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
    dir_list = [d.split('.')[0] for d in os.listdir(dir_path)]
    now = dt.datetime.now()
    all_codes = reduce(lambda result, c: result + map(lambda d: (c[0], c[1] + data_codes[d]), c[2]), codes, [])
    matching_codes = filter(lambda c: c[1] in dir_list, all_codes)
    columns = [
        'market_id',
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
        return [[code[0], code[1], r[0], r[1], r[2], r[3], r[4], r[4], r[5], r[6], now, now] for r in rows]

    map(lambda c: insert_values(q, values(c)), matching_codes)


if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        schema = sys.argv[1]
        schema_map = {
            'exchange': populate_exchange_table,
            'delivery_month': populate_delivery_month_table,
            'data_codes': populate_data_codes_table,
            'group': populate_group_table,
            'market': populate_market,
            'contract': populate_contracts,
            'continuous_back_adjusted': populate_continuous_back_adjusted,
            'continuous_spliced': populate_continuous_spliced,
            'spot_market': populate_spot_market
        }

        if schema in schema_map:
            schema_map.get(schema)(schema)
        else:
            print 'No schema of such name (%s) found.' % schema
            print 'Available schemas are: %s' % schema_map.keys()
    else:
        print 'Expected one argument - name of the table to insert data into'
