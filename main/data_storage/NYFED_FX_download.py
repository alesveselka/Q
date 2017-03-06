#!/usr/bin/python

# Automatic FX historical data download from "https://www.newyorkfed.org/xml/fx.html"

import os
import re
import csv
import requests
import xml.etree.ElementTree as ElementTree


def urls():
    reader = csv.reader(open('./resources/NY_FED_HistoricalFX.csv'), delimiter=',', quotechar='"')
    rows = [row for row in reader if re.match('^[a-zA-Z0-9]', row[0])][1:]
    sessions = ['Noon']  # ['10', 'Noon']
    mime_types = {'XML': 'text/xml', 'HTML': 'text/html'}
    file_template = './resources/NY_FED/%s.xml'
    api_template = 'https://www.newyorkfed.org/medialibrary/media/xml/data/fx/%s%s.xml'

    def download(symbol):
        print 'Requesting %s %s %s %s' % symbol
        response = requests.get(api_template % symbol[:-2])
        if response.headers['content-type'].startswith(mime_types['XML']):
            file_name = '__'.join([('{0}{1}' if symbol[2] == 'Base' else '{1}{0}').format(symbol[0], 'USD'), symbol[-1]])
            print 'Saving %s' % file_name
            file = open(file_template % file_name, 'w')
            file.write(response.text)
            file.close()
        else:
            print 'Skipping %s %s' % symbol

    map(download, [(r[0], s, r[2], r[3].replace(' to ', '_')) for r in rows for s in sessions])


def xml_to_csv():
    dir_path = './resources/NY_FED/'
    ns = 'http://www.newyorkfed.org/xml/schemas/FX/utility'
    dir_list = [d.split('.')[0] for d in os.listdir(dir_path)]

    def convert_file(file_name):
        print 'Converting %s' % file_name
        xml_file = open(''.join([dir_path, file_name, '.xml']), 'r')
        tree = ElementTree.fromstring(xml_file.read())
        values = [('{1}/{2}/{0}'.format(*e[0].text.split('-')), e[1].text) for e in tree.iter('{%s}Obs' % ns)]
        rows = [','.join([v[0], ('0.0,' * 3)[:-1], v[1]]) for v in values if v[1]]

        f = open(''.join([dir_path, file_name, '.csv']), 'w')
        f.write('Date,Open,High,Low,Close\n')
        f.write('\n'.join(rows))
        f.close()

    map(convert_file, dir_list)


if __name__ == '__main__':
    # TODO also compare with data from IMF!
    # urls()
    xml_to_csv()
