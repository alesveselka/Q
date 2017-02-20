#!/usr/bin/env python

import os
import re
import csv
import sys
import MySQLdb as mysql


def mysql_connection():
    # TODO cache
    return mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )


def csv_lines(file_name, exclude_header=True):
    """
    Read '*.csv' file by name passed in, and return non-empty rows
    """
    reader = csv.reader(open('./data/norgate/%s.csv' % file_name), delimiter=',', quotechar='"')
    rows = [row for row in reader if re.match('^[a-zA-Z0-9]', row[0])]
    return rows[1:] if exclude_header else rows


def query(table, columns, placeholders):
    return 'INSERT INTO `%s` (%s) VALUES (%s)' % (table, columns, placeholders)


def insert_values(operation, values):
    """
    Create MySQL database connection and cursor and execute operation for values passed in
    """
    connection = mysql_connection()
    with connection:
        cursor = connection.cursor()
        cursor.executemany(operation, values)


def populate_exchange_table(schema):
    code = 0
    ex_code = 1
    name = 2
    country = 4
    insert_values(
        query(schema, 'code, ex_code, name, country', "%s, %s, %s, %s"),
        [(l[code], l[ex_code], l[name], l[country]) for l in csv_lines(schema)]
    )


def populate_delivery_month_table(schema):
    insert_values(
        query(schema, 'code, name', "%s, %s"),
        csv_lines(schema)
    )


def populate_group_table(schema):
    insert_values(
        query(schema, 'name, standard', "%s, %s"),
        csv_lines(schema)
    )


def populate_market(schema):
    connection = mysql_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT name, id FROM `group` WHERE standard='Norgate'")
    groups = dict(cursor.fetchall())
    cursor.execute("SELECT name, id FROM `exchange`")
    exchanges = dict(cursor.fetchall())
    columns = {
        'name': 0,
        'code': 2,
        'exchange_id': 3,
        'group_id': 4,
        'contract_size': 5,
        'quotation': 6,
        'tick_size': 7,
        'tick_value': 8,
        'point_value': 9,
        'currency': 10,
        'last_trading_day': 11,
        'first_notice_day': 12
    }
    keys = columns.keys()
    markets = csv_lines(schema)

    def contains(key, data, market): return market[columns.get(key)] in data

    def print_lookup_error(m, key):
        print "[ERROR] Can't find '%s'. Skipping inserting '%s'" % (m[columns.get(key)], m[columns.get('name')])

    def replace_ids(m):
        m[columns.get('exchange_id')] = exchanges.get(m[columns.get('exchange_id')])
        m[columns.get('group_id')] = groups.get(m[columns.get('group_id')])

    map(lambda m: (
        (contains('exchange_id', exchanges, m) or print_lookup_error(m, 'exchange_id'))
        and (contains('group_id', groups, m) or print_lookup_error(m, 'group_id'))
        and replace_ids(m)
    ), markets)

    insert_values(
        query(schema, ','.join(keys), ("%s, " * len(keys))[:-2]),
        [[m[columns.get(k)] for k in keys] for m in markets]
    )


if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        schema = sys.argv[1]
        schema_map = {
            'exchange': populate_exchange_table,
            'delivery_month': populate_delivery_month_table,
            'group': populate_group_table,
            'market': populate_market
        }

        if schema in schema_map:
            schema_map.get(schema)(schema)
        else:
            print 'No schema of such name (%s) found.' % schema
    else:
        print 'Expect one argument - name of the table to insert data into'
