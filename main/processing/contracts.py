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


def index(key, data, position=0):
    return reduce(lambda i, d: i + 1 if d[position] <= key else i, data, 0)


def date(d):
    return dt.date(int(d[:4]), int(d[4:6]), int(d[6:]))


def query(table, columns, placeholders):
    return 'INSERT INTO `%s` (%s) VALUES (%s)' % (table, columns, placeholders)


def insert_values(operation, values):
    with mysql_connection:
        cursor = mysql_connection.cursor()
        cursor.executemany(operation, values)


def construct_continuous(schema, roll_strategy_name):
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT code, appendix FROM `data_codes`")
    data_codes = dict(cursor.fetchall())
    cursor.execute("SELECT id, code, data_codes FROM `market`")
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

    market_id = 0
    roll_out_month = 1
    roll_in_month = 2
    month = 3
    day = 4
    month_abbrs = [m for m in calendar.month_abbr]
    q = query(schema, ','.join(columns), ("%s, " * len(columns))[:-2])
    fn = {
        'continuous_adjusted': construct_adjusted,
        'continuous_spliced': construct_spliced
    }[schema]

    def values(code):
        contracts, rolls = contracts_data(
            code,
            roll_strategy_id,
            [(r[roll_out_month], r[roll_in_month], r[month], r[day]) for r in roll_schedule if r[market_id] == code[0]],
            dir_path,
            delivery_months,
            q,
            month_abbrs
        )
        data = fn(contracts, rolls)

        # diff = identical_to_norgate(data, schema, code[0])
        # print 'identical_to_norgate', diff

        return [[code[0], roll_strategy_id, code[1], d[0], d[1], d[2], d[3], d[4], d[4], d[5], d[6], now, now] for d in data]

    map(lambda c: insert_values(q, values(c)), matching_codes)
    # values((5, 'JY'))


def identical_to_norgate(series, table, market_id):
    columns = 'price_date, open_price, high_price, low_price, last_price, settle_price, volume, open_interest'
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT id FROM `roll_strategy` WHERE name = 'norgate'")
    norgate_id = cursor.fetchone()[0]
    cursor.execute("SELECT %s FROM %s WHERE market_id = '%s' AND roll_strategy_id = '%s'" % (
        columns,
        table,
        market_id,
        norgate_id
    ))
    norgate_series = cursor.fetchall()
    return len(norgate_series) == len(series) \
           and all([compare_rows(series[i[0]], norgate_series[i[0]]) for i in enumerate(series)])


def compare_rows(constructed, norgate):
    if Decimal(constructed[4]) != norgate[4]:
        print 'Wrong Data', date(constructed[0]), constructed[4], norgate[0], norgate[4]
    return date(constructed[0]) == norgate[0] \
        and Decimal(constructed[1]) == norgate[1] \
        and Decimal(constructed[2]) == norgate[2] \
        and Decimal(constructed[3]) == norgate[3] \
        and Decimal(constructed[4]) == norgate[4] \
        and Decimal(constructed[4]) == norgate[5] \
        and int(constructed[5]) == norgate[6] \
        and int(constructed[6]) == norgate[7]


def construct_spliced(contracts, rolls):
    roll_in_code = 5
    return reduce(lambda spliced, roll: spliced + contracts[roll[roll_in_code]], rolls, [])


def construct_adjusted(contracts, rolls):
    roll_in_code = 5
    gap_column = 3
    gap = 0
    result = []
    for roll in reversed(rolls):
        adjusted = [adjust_prices(row, gap) for row in contracts[roll[roll_in_code]]]
        result = adjusted + result
        gap += roll[gap_column]
    return result


def adjust_prices(row, price):
    prices = range(1, 5)
    return map(lambda i: Decimal(i[1]) + price if i[0] in prices else i[1], enumerate(row))


def contracts_data(code, roll_strategy_id, roll_schedule, dir_path, delivery_months, q, month_abbrs):
    price_date = 0
    last_price = 4
    last_contract_price = 0
    last_contract_code = None
    rolls = []
    continuous = {}
    schedule_months = [s[0] for s in roll_schedule]
    files = os.listdir(''.join([dir_path, code[1]]))
    file_names = [f for f in files if month_abbrs[index(f[-5].upper(), delivery_months)] in schedule_months]
    for f in sorted(file_names):
        contract_code = f[5:10]
        span = contract_span(f, roll_schedule, delivery_months, month_abbrs)
        rows = csv_lines(''.join([dir_path, code[1], '/', f]), exclude_header=False)
        contract_rows = [r for r in rows if span[0] <= date(r[price_date]) <= span[1]]
        if len(contract_rows):
            gap = Decimal(contract_rows[0][last_price]) - Decimal(last_contract_price) if last_contract_price else 0
            rolls.append((code[0], roll_strategy_id, date(contract_rows[0][price_date]), gap, last_contract_code, contract_code.upper()))
            continuous[contract_code.upper()] = contract_rows[1:] \
                if last_contract_code and date(continuous[last_contract_code][-1][0]) == date(contract_rows[0][0]) \
                else contract_rows
            last_contract_code = contract_code.upper()
            contract_roll_row = [r for r in rows if date(r[price_date]) >= span[1]]
            last_contract_price = contract_roll_row[0][last_price] if len(contract_roll_row) else 0

    return continuous, sorted(rolls, key=itemgetter(2))


def contract_span(contract_file, roll_schedule, delivery_months, month_abbrs):
    code_column = 0
    contract_year = int(contract_file[5:9])
    contract_month_code = contract_file[-5]
    contract_month_index = index(contract_month_code.upper(), delivery_months)
    contract_month = month_abbrs[contract_month_index]

    in_roll = [s for s in roll_schedule if s[1] == contract_month][0]
    in_month = in_roll[2]
    in_month_code = [m for m in delivery_months if m[2] == in_month][0][code_column]
    in_month_index = index(in_month_code, delivery_months)
    in_year = contract_year if contract_month_index - in_month_index > -1 else contract_year - 1

    out_roll = [s for s in roll_schedule if s[0] == contract_month][0]
    out_month = out_roll[2]
    out_month_code = [m for m in delivery_months if m[2] == out_month][0][code_column]
    out_month_index = index(out_month_code, delivery_months)
    out_year = contract_year if contract_month_index - out_month_index > -1 else contract_year - 1

    return dt.date(in_year, in_month_index, in_roll[3]), dt.date(out_year, out_month_index, out_roll[3])


if __name__ == '__main__':
    mysql_connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )

    # construct_continuous('continuous_spliced', 'standard_roll_1')
    # construct_continuous('continuous_adjusted', 'standard_roll_1')
