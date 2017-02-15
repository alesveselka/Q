#!/usr/bin/python

import re
import csv
import MySQLdb as mysql


def csv_lines(file_name, exclude_header=True):
    """
    Read '*.csv' file by name passed in, and return non-empty rows
    """
    reader = csv.reader(open('./data/norgate/%s.csv' % file_name), delimiter=',', quotechar='"')
    rows = [row for row in reader if re.match('^[a-zA-Z]', row[0])]
    return rows[1:] if exclude_header else rows


def insert_values(operation, values):
    """
    Create MySQL database connection and cursor and execute operation for values passed in
    """
    connection = mysql.connect(host='localhost', user='sec_user', passwd='root', db='norgate')
    with connection:
        cursor = connection.cursor()
        cursor.executemany(operation, values)


def populate_exchange_table():
    abbrev = 0
    name = 1
    insert_values(
        'INSERT INTO exchange (abbrev, name) VALUES (%s, %s)',
        [(l[abbrev], l[name]) for l in csv_lines('exchange')]
    )


def populate_delivery_month_table():
    insert_values(
        'INSERT INTO delivery_month (code, name) VALUES (%s, %s)',
        csv_lines('delivery_month')
    )


def populate_group_table():
    insert_values(
        'INSERT INTO `group` (name, standard) VALUES (%s, %s)',
        csv_lines('group')
    )


if __name__ == '__main__':
    populate_group_table()
