#!/usr/bin/python

# Automatic FX historical data download from "https://www.newyorkfed.org/xml/fx.html"

import requests


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


if __name__ == '__main__':
    urls()
