#!/usr/bin/env python

import os
import csv
import re
import json
import calendar
import datetime as dt
import MySQLdb as mysql
from decimal import Decimal
from operator import itemgetter


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


def construct_continuous():
    roll_strategy_name = 'standard_roll_1'
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT code, appendix FROM `data_codes`")
    data_codes = dict(cursor.fetchall())
    cursor.execute("SELECT id, code, data_codes, volume_offset, oi_offset FROM `market`")
    codes = cursor.fetchall()
    cursor.execute("SELECT code, name, short_name FROM `delivery_month`")
    delivery_months = cursor.fetchall()
    cursor.execute("SELECT id, name, params FROM `roll_strategy` WHERE name = '%s'" % roll_strategy_name)
    roll_strategy = cursor.fetchone()
    roll_strategy_id = roll_strategy[0]
    roll_strategy_params = json.loads(roll_strategy[2])
    cursor.execute(
        "SELECT market_id, roll_out_month, roll_in_month, month, day FROM `standard_roll_schedule` WHERE name = '%s'" \
        % roll_strategy_params['schedule']
    )
    roll_schedule = cursor.fetchall()
    dir_path = './resources/Norgate/data/Futures/Contracts/_Text/'
    dir_list = os.listdir(dir_path)
    now = dt.datetime.now()
    all_codes = reduce(lambda result, c: result + map(lambda d: (c[0], c[1] + data_codes[d], c[3], c[4]), c[2]), codes, [])
    matching_codes = filter(lambda c: c[1] in dir_list, all_codes)
    columns = [
        'market_id',
        'roll_strategy_id',
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
    q = query('continuous_adjusted', ','.join(columns), ("%s, " * len(columns))[:-2])
    market_id = 0
    roll_out_month = 1
    roll_in_month = 2
    month = 3
    day = 4
    month_abbrs = [m for m in calendar.month_abbr]

    populate_symbol(
        now,
        (37L, 'ES', 'I', 0, -1),  # TODO don't need the offsets
        # (106L, 'WT', 'I', 0, -1),
        roll_strategy_id,
        [(r[roll_out_month], r[roll_in_month], r[month], r[day]) for r in roll_schedule if r[market_id] == 37],
        dir_path,
        delivery_months,
        q,
        month_abbrs
    )

    # for code in matching_codes:
    #     populate_symbol(now, code, dir_path, delivery_months, q)


def populate_symbol(now, code, roll_strategy_id, roll_schedule, dir_path, delivery_months, q, month_abbrs):
    files = os.listdir(''.join([dir_path, code[1]]))

    def values(file_name):
        delivery = file_name[5:10]
        year = int(delivery[:-1])
        month = index(delivery[-1], delivery_months)
        delivery_date = dt.date(year, month, calendar.monthrange(year, month)[1])
        rows = csv_lines(''.join([dir_path, code[1], '/', file_name]), exclude_header=False)
        return rows
        # price_date = 0
        # open_price = 1
        # high_price = 2
        # low_price = 3
        # last_price = 4
        # settle_price = 4
        # volume = 5
        # open_interest = 6
        # return [[
        #     code[0],
        #     roll_strategy_id,
        #     delivery_date,
        #     delivery_date,
        #     code[1] + delivery,
        #     r[price_date],
        #     r[open_price],
        #     r[high_price],
        #     r[low_price],
        #     r[last_price],
        #     r[settle_price],
        #     r[volume],
        #     r[open_interest],
        #     now,
        #     now,
        #     month_abbrs[month]
        # ] for r in rows]

    # map(lambda f: insert_values(q, values(f)), files)

    price_date = 0
    last_price = 4
    last_contract_price = 0
    last_contract_code = None
    contract_code = None
    rolls = []
    continuous = []
    schedule_months = [s[0] for s in roll_schedule]
    file_names = [f for f in files if month_abbrs[index(f[-5], delivery_months)] in schedule_months]
    for f in sorted(file_names):
        contract_code = f[5:10]
        span = contract_span(f, roll_schedule, delivery_months, month_abbrs)
        rows = csv_lines(''.join([dir_path, code[1], '/', f]), exclude_header=False)
        contract_rows = [r for r in rows if span[0] <= date(r[price_date]) < span[1]]
        if len(contract_rows):
            gap = Decimal(contract_rows[0][last_price]) - Decimal(last_contract_price) if last_contract_price else 0
            rolls.append((code[0], roll_strategy_id, contract_rows[0][price_date], gap, last_contract_code, contract_code))
            last_contract_code = contract_code
            contract_roll_row = [r for r in rows if date(r[price_date]) >= span[1]]
            last_contract_price = contract_roll_row[0][last_price] if len(contract_roll_row) else 0
            continuous += contract_rows

    # for c in continuous:
    #     print c

    for r in rolls:
        print r

    for s in roll_schedule:
        print s


# def compare_continuous()


def contract_span(contract_file, roll_schedule, delivery_months, month_abbrs):
    contract_year = int(contract_file[5:9])
    contract_month_code = contract_file[-5]
    contract_month_index = index(contract_month_code, delivery_months)
    contract_month = month_abbrs[contract_month_index]

    in_roll = [s for s in roll_schedule if s[1] == contract_month][0]
    in_month = in_roll[2]
    in_month_code = [m for m in delivery_months if m[2] == in_month][0][0]
    in_month_index = index(in_month_code, delivery_months)
    in_year = contract_year if contract_month_index - in_month_index > -1 else contract_year - 1

    out_roll = [s for s in roll_schedule if s[0] == contract_month][0]
    out_month = out_roll[2]
    out_month_code = [m for m in delivery_months if m[2] == out_month][0][0]
    out_month_index = index(out_month_code, delivery_months)
    out_year = contract_year if contract_month_index - out_month_index > -1 else contract_year - 1

    return dt.date(in_year, in_month_index, in_roll[3]), dt.date(out_year, out_month_index, out_roll[3])


def index(key, data, position=0):
    return reduce(lambda i, d: i + 1 if d[position] <= key else i, data, 0)


def date(d):
    return dt.date(int(d[:4]), int(d[4:6]), int(d[6:]))


if __name__ == '__main__':
    mysql_connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )

    construct_continuous()
