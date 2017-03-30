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


def aud_immediate():
    """
    Fetches and parses cash-rate page of Reserve Bank of Australia
    The table rows are as follow:
    +-------------------+-------------------------------+-------------------------------+
    | Effective Date    | Change in Percentage points   | New cash rate target Per cent |
    +-------------------+-------------------------------+-------------------------------+
    | 8 Mar 2017        | 0.00                          | 1.50                          |
    +-------------------+-------------------------------+-------------------------------+

    :return: List of tuples (date, float)
    """
    response = requests.get('http://www.rba.gov.au/statistics/cash-rate/')
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    rows = soup.select('#datatable > tbody > tr')
    rates = [[r.select('th')[0].text, r.select('td')[-1].text] for r in rows]
    months = {k: i for i, k in enumerate(calendar.month_abbr) if k}
    result = []

    for r in rates:
        date = dt.date(*map(lambda x: int(x) if re.match('^[0-9]', x) else months[x], reversed(r[0].split(' '))))
        rate = [r for r in re.sub(r'[a-zA-Z\s]', ',', r[1]).split(',') if r]
        result.append((date, float(rate[0]) if len(rate) == 1 else sum(map(float, rate)) / len(rate)))

    # TODO reverse?
    return result


def aud_three_months(connection):
    """
    Calculates rates from Futures data (inverted yield: 100 - interest date)

    :param connection:  MySQL connector's connection instance
    :return:            List of tuples (date, float)
    """
    cursor = connection.cursor()
    cursor.execute("SELECT price_date, settle_price FROM `continuous_spliced` WHERE code = 'YIR'")
    data = cursor.fetchall()

    return [(d[0], float(100-d[1])) for d in data]


if __name__ == '__main__':
    mysql_connection = mysql.connect('localhost', 'sec_user', 'root', 'norgate')

    # aud_immediate()
    aud_three_months(mysql_connection)
