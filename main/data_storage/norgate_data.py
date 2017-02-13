#!/usr/bin/python

import os
import re
import MySQLdb as mysql


def populate_exchange_table():
    """
    Parse Norgate 'names' text file and populate exchange table with extracted info
    """
    file_object = open(os.path.abspath('c:/Norgate/data/Stocks/_Text/names.txt'))
    lines = file_object.readlines()
    stock_symbols = filter(lambda l: re.match('^[a-zA-Z]', l), lines)
    codes = set()

    reduce(lambda s, l: codes.add(re.sub('[\",\n]', '', l.split(',')[2])), stock_symbols)

    values = map(lambda c: (c, re.split('[^a-zA-Z]', c)), codes)

    connection = mysql.connect(host='localhost', user='sec_user', passwd='root', db='norgate')
    with connection:
        cursor = connection.cursor()
        cursor.executemany(
            'INSERT INTO exchange (abbrev, name, country) VALUES (%s, %s, %s)',
            [(v[-1][-1], v[0].split('\\')[-1], v[-1][0]) for v in values]
        )


if __name__ == '__main__':
    populate_exchange_table()
