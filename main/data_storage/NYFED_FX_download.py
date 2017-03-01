#!/usr/bin/python

# Automatic FX historical data download from "https://www.newyorkfed.org/xml/fx.html"

import os
import requests
import xml.etree.ElementTree as ElementTree


def urls():
    sessions = ['10', 'Noon']
    mime_types = {'XML': 'text/xml', 'HTML': 'text/html'}
    file_template = './resources/NY_FED/%s%s.xml'
    api_template = 'https://www.newyorkfed.org/medialibrary/media/xml/data/fx/%s%s.xml'
    codes = ['ATS', 'AUD', 'BEF', 'BRL', 'CAD', 'CHF', 'CNY', 'DEM', 'DKK', 'ESP', 'EUR', 'FIM', 'FRF', 'GBP', 'GRD', 'HKD', 'IEP', 'INR', 'ITL', 'JPY', 'KRW', 'LKR', 'MXN', 'MYR', 'NLG', 'NOK', 'NZD', 'PTE', 'SEK', 'SGD', 'THB', 'TWD', 'VEB', 'ZAR']

    def download(symbol):
        print 'Requesting %s %s' % symbol
        response = requests.get(api_template % symbol)
        if response.headers['content-type'].startswith(mime_types['XML']):
            print 'Saving %s %s' % symbol
            # file = open(file_template % symbol, 'w')
            # file.write(response.text)
            # file.close()
        else:
            print 'Skipping %s %s' % symbol

    # map(download, [(c, s) for c in codes for s in sessions])
    download([(c, s) for c in codes for s in sessions][1])


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
    # urls()
    xml_to_csv()
