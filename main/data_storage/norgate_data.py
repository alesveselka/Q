#!/usr/bin/env python

import os
import re
import csv
import sys
import MySQLdb as mysql


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
    connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )
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


if __name__ == '__main__':
    if len(sys.argv) == 2 and len(sys.argv[1]):
        schema = sys.argv[1]
        schema_map = {
            'exchange': populate_exchange_table,
            'delivery_month': populate_delivery_month_table,
            'group': populate_group_table
        }

        if schema in schema_map:
            schema_map.get(schema)(schema)
        else:
            print 'No schema of such name (%s) found.' % schema
    else:
        print 'Expect one argument - name of the table to insert data into'
