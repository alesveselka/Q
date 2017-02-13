#!/usr/bin/python

import os
import re
import MySQLdb as mysql


def populate_exchange_table():
    """
    Parse Norgate 'names' text file and populate exchange table with extracted info
    """
    # TODO use own file with clear structure
    file_object = open(os.path.abspath('c:/Norgate/data/Stocks/_Text/names.txt'))
    lines = file_object.readlines()
    codes = [l.split(',')[2] for l in lines if re.match('^[a-zA-Z]', l)]
    code_set = set([re.sub('[\",\n]', '', c) for c in codes])
    values = [(c, re.split('[^a-zA-Z]', c)) for c in code_set]

    connection = mysql.connect(host='localhost', user='sec_user', passwd='root', db='norgate')
    with connection:
        cursor = connection.cursor()
        cursor.executemany(
            'INSERT INTO exchange (abbrev, name, country) VALUES (%s, %s, %s)',
            [(v[-1][-1], v[0].split('\\')[-1], v[-1][0]) for v in values]
        )


def populate_delivery_month_table():
    connection = mysql.connect(host='localhost', user='sec_user', passwd='root', db='norgate')
    values = [
        'F:January',
        'G:February',
        'H:March',
        'J:April',
        'K:May',
        'M:June',
        'N:July',
        'Q:August',
        'U:September',
        'V:October',
        'X:November',
        'Z:December'
    ]

    with connection:
        cursor = connection.cursor()
        cursor.executemany(
            'INSERT INTO delivery_month (code, name) VALUES (%s, %s)',
            [v.split(':') for v in values]
        )



if __name__ == '__main__':
    populate_delivery_month_table()
