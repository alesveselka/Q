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
    rows = [row for row in reader if re.match('^[a-zA-Z]', row[0])]
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
    cursor.execute("SELECT id, name FROM `group` WHERE standard='Norgate'")
    groups = dict([[g[1], int(g[0])] for g in cursor.fetchall()])
    cursor.execute("SELECT id, name FROM `exchange`")
    exchanges = dict([[e[1], int(e[0])] for e in cursor.fetchall()])

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
    markets = csv_lines(schema)
    for m in markets:
        if m[columns.get('exchange_id')] in exchanges:
            if m[columns.get('group_id')] in groups:
                m[columns.get('exchange_id')] = exchanges.get(m[columns.get('exchange_id')])
                m[columns.get('group_id')] = groups.get(m[columns.get('group_id')])
            else:
                print "Can't find group: %s. Skipping inserting %s" % (m[columns.get('group_id')], m[columns.get('name')])
        else:
            print "Can't find exchange: %s. Skipping inserting %s" % (m[columns.get('exchange_id')], m[columns.get('name')])

    q = query(schema, 'name, code, exchange_id, group_id, contract_size, quotation, tick_size, tick_value, point_value, currency, last_trading_day, first_notice_day', ("%s, " * 12)[:-2])
    print 'Query: %s' % q
    print 'Markets: %s' % [[
                               m[columns.get('name')],
                               m[columns.get('code')],
                               int(m[columns.get('exchange_id')]),
                               int(m[columns.get('group_id')]),
                               m[columns.get('contract_size')],
                               m[columns.get('quotation')],
                               m[columns.get('tick_size')],
                               float(m[columns.get('tick_value')]),
                               float(m[columns.get('point_value')]),
                               m[columns.get('currency')],
                               m[columns.get('last_trading_day')],
                               m[columns.get('first_notice_day')]
                           ] for m in markets[:1]]

    insert_values(
        q,
        [[
             m[columns.get('name')],
             m[columns.get('code')],
             int(m[columns.get('exchange_id')]),
             int(m[columns.get('group_id')]),
             m[columns.get('contract_size')],
             m[columns.get('quotation')],
             m[columns.get('tick_size')],
             float(m[columns.get('tick_value')]),
             float(m[columns.get('point_value')]),
             m[columns.get('currency')],
             m[columns.get('last_trading_day')],
             m[columns.get('first_notice_day')]
         ] for m in markets]
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
