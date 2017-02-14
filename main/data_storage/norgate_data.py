#!/usr/bin/python

import re
import csv
import MySQLdb as mysql


def csv_lines(file_name, exclude_header=True):
    reader = csv.reader(open('./data/norgate/%s.csv' % file_name), delimiter=',', quotechar='"')
    rows = [row for row in reader if re.match('^[a-zA-Z]', row[0])]
    return rows[1:] if exclude_header else rows


def insert_values(operation, values):
    connection = mysql.connect(host='localhost', user='sec_user', passwd='root', db='norgate')
    with connection:
        cursor = connection.cursor()
        cursor.executemany(operation, [v for v in values])


def populate_exchange_table():
    insert_values(
        'INSERT INTO exchange (abbrev, name) VALUES (%s, %s)',
        [(l[0], l[1]) for l in csv_lines('exchange')]
    )


def populate_delivery_month_table():
    insert_values(
        'INSERT INTO delivery_month (code, name) VALUES (%s, %s)',
        csv_lines('delivery_month')
    )


def populate_group_table():
    """
    Parse Norgate example csv and populate 'group' table with extracted data
    """


if __name__ == '__main__':
    populate_exchange_table()
