#!/usr/bin/python

import os
import re
import csv


def read_data(dir_path, file_name):
    reader = csv.reader(open('%s%s' % (dir_path, file_name)), delimiter=',', quotechar='"')
    rows = [row[1:] for row in reader if re.match('^[a-zA-Z0-9]', row[0])][1:]
    header = dict(zip(rows[0], range(len(rows[0]))))
    data = rows[1:]
    pairs = [r for r in rows[0] if re.match('[A-Z]{3}/[A-Z]{3}', r)]

    return header, data, pairs


def generate_csvs(dir_path, header, data, pairs):
    def file_name(pair, rows):
        return '%s__%s_%s.csv' % tuple(
            [pair.replace('/', '')] +
            ['{2}-{0}-{1}'.format(*r.split(',')[0].split('/')) for r in [rows[0], rows[-1]]]
        )

    def generate_csv(pair):
        values = [('{1}/{2}/{0}'.format(*d[0].split('/')), d[header[pair]]) for d in data]
        rows = [','.join([v[0], ('0.0,' * 3)[:-1], v[1]]) for v in values if v[1]]

        if len(rows):
            name = file_name(pair, rows)
            print 'Generating %s' % name

            f = open(''.join([dir_path, 'generated/', name]), 'w')
            f.write('Date,Open,High,Low,Close\n')
            f.write('\n'.join(rows))
            f.close()

    map(generate_csv, pairs)


if __name__ == '__main__':
    dir_path = './resources/UBC/'
    dir_list = [path for path in os.listdir(dir_path) if re.match('^ECU', path)]

    map(lambda file_name: generate_csvs(dir_path, *read_data(dir_path, file_name)), dir_list)
