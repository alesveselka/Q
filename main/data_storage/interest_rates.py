#!/usr/bin/python

# Swiss Franc (https://data.snb.ch/en/topics/ziredev#!/cube/zimoma?fromDate=1972-02&toDate=2017-02&dimSel=D0(SARON,1TGT,1M,3M0))

import datetime as dt
import os
import re
import csv
import json
import calendar
import requests
import bs4
import MySQLdb as mysql
from collections import defaultdict


def page_soup(url):
    """
    Fetch url and returns parsed 'soup'

    :param url:     URL to fetch and parse
    :return:        BeautifulSoup object
    """
    response = requests.get(url)
    return bs4.BeautifulSoup(response.text, "html.parser")


def fred_data(series_id):
    """
    Fetch and transform data from FRED API
    Example of returned JSON value is:
    {
        "realtime_start": "2017-03-31",
        "realtime_end": "2017-03-31",
        "observation_start": "1600-01-01",
        "observation_end": "9999-12-31",
        "units": "lin",
        "output_type": 1,
        "file_type": "json",
        "order_by": "observation_date",
        "sort_order": "asc",
        "count": 8146,
        "offset": 0,
        "limit": 100000,
        "observations": [
            {
                "realtime_start": "2017-03-31",
                "realtime_end": "2017-03-31",
                "date": "1986-01-02",
                "value": "11.87500"
            },
            {
                "realtime_start": "2017-03-31",
                "realtime_end": "2017-03-31",
                "date": "1986-01-03",
                "value": "11.87500"
            }
        ]}

    :return: List of tuples (date, float)
    """
    api_url = 'https://api.stlouisfed.org/fred/series/observations'
    params = 'series_id=%s&api_key=%s&file_type=json' % (series_id, os.environ['FRED_API_KEY'])
    response = requests.get('%s?%s' % (api_url, params))
    data = json.loads(response.text)
    result = []
    rate = 0

    for o in data['observations']:
        rate = float(o['value']) if o['value'] != '.' else rate
        last_date = dt.date(*map(int, o['date'].split('-')))
        result.append((last_date, rate))

    return result


def futures_yield(futures_code):
    """
    Calculates and returns interest rates calculated from Futures inverted yield

    :param futures_code:    String, Futures symbol code
    :return:                List of tuples (date, float)
    """
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT price_date, settle_price FROM `continuous_spliced` WHERE code = '%s'" % futures_code)
    return [(d[0], float(100-d[1])) for d in cursor.fetchall()]


def combine_fred_and_futures(fred_series_id, futures_code):
    """
    Fetches FRED data and conditionally append data calculated from Futures data

    :param fred_series_id:  String, ID of the FRED series
    :param futures_code:    String, Futures symbol code
    :return:                List of tuples (date, float)
    """
    data = fred_data(fred_series_id)
    now = dt.datetime.now().date()
    last_date = data[-1][0]
    return data + [y for y in futures_yield(futures_code) if y[0] > last_date] if now > last_date else data


def aud_immediate():
    """
    Fetches and parses cash-rate page of Reserve Bank of Australia
    The table rows are as follow:
    +-------------------+-------------------------------+-------------------------------+
    | Effective Date    | Change in Percentage points   | New cash rate target Per cent |
    +-------------------+-------------------------------+-------------------------------+
    | 8 Mar 2017        | 0.00                          | 1.50                          |
    +-------------------+-------------------------------+-------------------------------+

    :return:        List of tuples (date, float)
    """
    soup = page_soup('http://www.rba.gov.au/statistics/cash-rate/')
    rows = soup.select('#datatable > tbody > tr')
    rates = [[r.select('th')[0].text, r.select('td')[-1].text] for r in rows]
    result = []

    for r in rates:
        date = dt.date(*map(lambda x: int(x) if re.match('^[0-9]', x) else months[x], reversed(r[0].split(' '))))
        rate = [r for r in re.sub(r'[a-zA-Z\s]', ',', r[1]).split(',') if r]
        result.append((date, float(rate[0]) if len(rate) == 1 else sum(map(float, rate)) / len(rate)))

    # TODO reverse?
    return result


def aud_three_months():
    """
    Return futures yield data for 'YIR' symbol

    :return:    List of tuples (date, float)
    """
    return futures_yield('YIR')


def gbp_immediate():
    """
    Fetch and parse Bank of England page with interest rates.
    The table contains only records of interest rate changes, not regular interval!
    +-------------------+-----------+
    | Date Changed      | Rate      |
    +-------------------+-----------+
    | Thu, 04 Aug 2016  | 0.2500    |
    +-------------------+-----------+

    :return:    List of tuples (date, float)
    """
    soup = page_soup('http://www.bankofengland.co.uk/boeapps/iadb/Repo.asp?Travel=NIxRPx')
    rows = soup.select('#editorial > table > tr')
    rates = [r.select('td') for r in rows]
    result = []

    for r in [r for r in rates if len(r)]:
        data_date = r[0].text.split(', ')[1]
        date = dt.date(*map(lambda x: int(x) if re.match('^[0-9]', x) else months[x], reversed(data_date.split(' '))))
        result.append((date, float(r[1].text)))

    return result


def gbp_three_months():
    """
    Return GBP data combination

    :return: List of tuples (date, float)
    """
    return combine_fred_and_futures('GBP3MTD156N', 'LSS')


def cad_immediate():
    """
    Return result of FRED data with ID for canadian interest rates

    :return: List of tuples (date, float)
    """
    return fred_data('INTGSTCAM193N')


def cad_three_months():
    """
    Return CAD data combination

    :return: List of tuples (date, float)
    """
    return combine_fred_and_futures('IR3TIB01CAM156N', 'BAX')


def eur():
    """
    Download, parse and construct lists of short-term and mid-term interest rates
    from range of pages across the years.

    For short-term, I use either monthly-overnight or yearly-overnight, yearly-1-week,
    yearly-2-weeks, yearly-1-month term as approximation depending what is available in particular year.
    For mid-term I use typical 3-months rate.

    :return:    Two lists of tuples (date, float)
    """
    url = 'http://www.global-rates.com/interest-rates/libor/european-euro/%s.aspx'
    months = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
    rates = defaultdict(list)
    shorts = []

    for year in range(1989, 2018):
        soup = page_soup(url % year)
        rows = soup.select('.tabledata1, .tabledata2')
        shorts_monthly = []
        shorts_yearly = []

        for r in rows:
            tds = [td.text for td in r.select('td')]
            name = 'Y_' + tds[0].split(' - ')[1].replace(' ', '_') if 'LIBOR' in tds[0] else 'M_' + re.sub('\W', '', tds[0])
            date = dt.date(year, 1, 1) if name[0] == 'Y' else dt.date(year, months[name.split('_')[1]], 1)
            if tds[1] != '-':
                value = float(re.sub('\D[% ]', '', tds[1]))
                rates[name].append((date, value))

                if name.startswith('M_'):
                    shorts_monthly.append((date, value))
                elif any(name == i for i in ['Y_1_week', 'Y_2_weeks', 'Y_1_month']):
                    shorts_yearly.append((date, value))

        if len(shorts_monthly):
            shorts += shorts_monthly
        else:
            shorts += [shorts_yearly[0]] if len(shorts_yearly) else []

    return sorted(shorts), rates['Y_3_months']


def eur_three_months(yearly_data):
    """
    Concat yearly data with daily ones on date where daily data start

    :param yearly_data:     list of tuples (date, float)
    :return:                list of tuples (date, float)
    """
    daily_data = fred_data('EUR3MTD156N')
    first_date = daily_data[0][0]

    return [y for y in yearly_data if y[0] <= first_date] + daily_data


def jpy_immediate():
    """
    Fetch and parse Bank of Japan page with interest rates.
    Table example:
    +-----------+------------------------------------------------+---------------------------------------------------+
    | Date      | The Basic Discount Rate and Basic Loan Rate    | Call Rate, Uncollateralized Overnight/Average     |
    +-----------+------------------------------------------------+---------------------------------------------------+
    | 2017/02   | 0.3                                            | -0.038                                            |
    | 2017/03   | 0.3                                            | ND                                                |
    +-----------+------------------------------------------------+---------------------------------------------------+

    :return:    List of tuples (date, float)
    """
    soup = page_soup('http://www.stat-search.boj.or.jp/ssi/html/nme_R020MM.5269.20170331235215.02.html')
    rows = soup.select('.tbl > table > tr')
    rates = [r.select('td') for r in rows]
    result = []

    for r in rates[1:]:
        tds = [td.text for td in r]
        if 'ND' not in tds[2]:
            data_date = dt.date(*map(int, tds[0].split('/') + [1]))
            result.append((data_date, float(tds[2])))

    return result


def jpy_three_months():
    """
    Return result of FRED data with ID for japanese 3-month interest rates

    :return: List of tuples (date, float)
    """
    return fred_data('JPY3MTD156N')


def chf_immediate():
    """
    Parse and return CSV table with CHF interest rates
    Table example:
    +-----------+-----------------------------------------------+-----------+
    | Date      | SARON     | Call money rate (Tomorrow next)   | 3-month   |
    +-----------+-----------------------------------------------+-----------+
    | 2017-02   | -0.729    | -0.950                            | -0.726    |
    +-----------+-----------------------------------------------+-----------+

    :return:    List of tuples (date, float)
    """
    reader = csv.reader(open('./data/CHF_interest_rates.csv'), delimiter=',', quotechar='"')
    rows = [row for row in reader if re.match('^[a-zA-Z0-9]', row[0])][1:]
    result = [(dt.date(*map(int, r[0].split('-') + [1])), r[1] if r[1] else r[2]) for r in rows]

    return result


def chf_three_months():
    """
    Return CHF data combination

    :return: List of tuples (date, float)
    """
    return combine_fred_and_futures('CHF3MTD156N', 'LES')


if __name__ == '__main__':
    months = {k: i for i, k in enumerate(calendar.month_abbr) if k}
    mysql_connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )

    # TODO ensure same order for all lists
    # TODO resolve multiple intervals (Daily, Monthly, Irregularly, ...)
    # TODO for intervals > daily, make sure the data is unified - beginning of month VS end of month ...

    # aud_immediate()
    # aud_three_months()
    # gbp_immediate()
    # gbp_three_months()
    # cad_immediate()
    # cad_three_months()
    # eur_immediate, eur_three = eur()
    # eur_three_months(eur_three)
    # jpy_immediate()
    # jpy_three_months()
    # chf_immediate()
    chf_three_months()
