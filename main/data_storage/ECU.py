#!/usr/bin/python

import os
import re
import csv
import time
import random
import requests
from collections import defaultdict


def download_eur_pairs(target_dir_path):
    def parameters(symbol, first_year, last_year, notation):
        return {
            'b': 'EUR',
            'c': symbol,
            'fd': '1',
            'fm': '1',
            'fy': first_year,
            'ld': '31',
            'lm': '12',
            'ly': last_year,
            'y': 'daily',
            'q': notation,
            'f': 'csv'
        }

    def download(params):
        response = requests.get('http://fx.sauder.ubc.ca/cgi/fxdata', params)
        name = '%s__%s-01-01_%s-12-31.csv' % (
            ('{0}{1}' if params['q'] == 'price' else '{1}{0}').format(params['b'], params['c']),
            params['fy'],
            params['ly']
        )
        print 'Download: %s' % name

        f = open(''.join([target_dir_path, name]), 'w')
        f.write(response.text)
        f.close()

        time.sleep(random.randint(5, 15))

    map(lambda pair: download(parameters(*pair)), [
        (code, r.split(':')[0], r.split(':')[1], notation)
        for code in ['CHF']  # ['AUD', 'GBP', 'CAD', 'JPY', 'CHF', 'USD']
        for r in ['1993:1996', '1997:2000']
        for notation in ['price', 'volume']
    ])


def read_data(dir_path, file_name):
    reader = csv.reader(open('%s%s' % (dir_path, file_name)), delimiter=',', quotechar='"')
    rows = [row[1:] for row in reader if re.match('^[a-zA-Z0-9]', row[0])][1:]
    header = dict(zip(rows[0], range(len(rows[0]))))
    data = rows[1:]
    pairs = [r for r in rows[0] if re.match('[A-Z]{3}/[A-Z]{3}', r)]

    return header, data, pairs


def file_name(pair, rows):
    return '%s__%s_%s.csv' % tuple(
        [pair.replace('/', '')] +
        ['{2}-{0}-{1}'.format(*r.split(',')[0].split('/')) for r in rows]
    )


def generate_csvs(dir_path, header, data, pairs):
    def generate_csv(pair):
        correct_pair = '{1}{0}'.format(*pair.split('/'))
        values = [('{1}/{2}/{0}'.format(*d[0].split('/')), d[header[pair]]) for d in data]
        rows = [','.join([v[0], ('0.0,' * 3)[:-1], v[1]]) for v in values if v[1]]

        if len(rows):
            name = file_name(correct_pair, [rows[0], rows[-1]])
            print 'Generating %s' % name

            f = open(''.join([dir_path, 'generated/split/', name]), 'w')
            f.write('Date,Open,High,Low,Close\n')
            f.write('\n'.join(rows))
            f.close()

    map(generate_csv, pairs)


def concat_files(source_dir_path, target_dir_path):
    def append_file(d, f):
        d[f[:6]].append(f)
        return d

    def generate_csv(item):
        files = item[1]
        rows = []

        for f in files:
            reader = csv.reader(open(''.join([source_dir_path, f])), delimiter=',', quotechar='"')
            rows += [','.join(row) for row in reader][1:]

        name = file_name(item[0], [rows[0], rows[-1]])
        print 'Generating %s' % name
        full_file = open(''.join([target_dir_path, name]), 'w')
        full_file.write('Date,Open,High,Low,Close\n')
        full_file.write('\n'.join(rows))
        full_file.close()

    pairs = reduce(append_file, os.listdir(source_dir_path), defaultdict(list))

    map(generate_csv, pairs.items())


if __name__ == '__main__':
    dir_path = './resources/UBC/'
    dir_list = os.listdir(dir_path)
    ecu_list = [path for path in dir_list if re.match('^ECU', path)]
    eur_list = [path for path in dir_list if re.match('^[A-Z]{6}', path)]

    # download_eur_pairs(dir_path)

    map(lambda f: generate_csvs(dir_path, *read_data(dir_path, f)), ecu_list + eur_list)

    concat_files(
        ''.join([dir_path, 'generated/split/']),
        ''.join([dir_path, 'generated/full/'])
    )
