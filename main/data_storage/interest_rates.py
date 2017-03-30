#!/usr/bin/python

# Australia Cash Rate (http://www.rba.gov.au/statistics/cash-rate/)
# Euro LIBOR (http://www.global-rates.com/interest-rates/libor/european-euro/2017.aspx)
# Japanese Yen
#       (http://www.stat-search.boj.or.jp/ssi/mtshtml/ir01_d_1_en.html)
#       (http://www.stat-search.boj.or.jp/ssi/cgi-bin/famecgi2?cgi=$ap181g3f_en)
# Swiss Franc (https://data.snb.ch/en/topics/ziredev#!/cube/zimoma?fromDate=1972-02&toDate=2017-02&dimSel=D0(SARON,1TGT,1M,3M0))

import datetime as dt
import re
import calendar
import requests
import bs4
import MySQLdb as mysql


def page(url):
    """
    Fetch url and returns parsed 'soup'

    :param url:     URL to fetch and parse
    :return:        BeautifulSoup object
    """
    response = requests.get(url)
    return bs4.BeautifulSoup(response.text, "html.parser")


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
    soup = page('http://www.rba.gov.au/statistics/cash-rate/')
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
    Calculates rates from Futures data (inverted yield: 100 - interest date)

    :return:            List of tuples (date, float)
    """
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT price_date, settle_price FROM `continuous_spliced` WHERE code = 'YIR'")
    data = cursor.fetchall()

    return [(d[0], float(100-d[1])) for d in data]


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
    soup = page('http://www.bankofengland.co.uk/boeapps/iadb/Repo.asp?Travel=NIxRPx')
    rows = soup.select('#editorial > table > tr')
    rates = [r.select('td') for r in rows]
    result = []

    for r in [r for r in rates if len(r)]:
        data_date = r[0].text.split(', ')[1]
        date = dt.date(*map(lambda x: int(x) if re.match('^[0-9]', x) else months[x], reversed(data_date.split(' '))))
        result.append((date, float(r[1].text)))

    return result


if __name__ == '__main__':
    months = {k: i for i, k in enumerate(calendar.month_abbr) if k}
    mysql_connection = mysql.connect('localhost', 'sec_user', 'root', 'norgate')

    # TODO resolve multiple intervals (Daily, Monthly, Irregularly, ...)

    # aud_immediate()
    # aud_three_months(mysql_connection)
    gbp_immediate()
