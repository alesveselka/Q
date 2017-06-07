#!/usr/bin/python

import datetime as dt
import os
import requests
import bs4
import MySQLdb as mysql


def page_soup(url):
    """
    Fetch url and returns parsed 'soup'

    :param url:     URL to fetch and parse
    :return:        BeautifulSoup object
    """
    response = requests.get(url)
    return bs4.BeautifulSoup(response.text, "html.parser")


def values(element):
    """
    Parse XML element and return tuple with values
    
    :param element:     element to parse
    :return:            tuple(date, description, list of exchanges, country)
    """
    date = element.find('date').text
    exchanges = element.find_all('exchange')
    return (
        dt.date(int(date[:4]), int(date[5:7]), int(date[8:])),
        element.find('holiday_description').text,
        ','.join([e.text for e in exchanges]) if len(exchanges) else None,
        element.find('country').text
    )


def scrape_holidays():
    """
    Scrape holidays data from CSI website adn insert them into DB
    """
    months = range(1, 13)
    years = range(1950, 2020)
    columns = ['date', 'description', 'exchanges', 'country']
    sql = "INSERT INTO holidays (%s) VALUES (%s);" % (', '.join(columns), ('%s, ' * len(columns))[:-2])

    for date in [(y, m) for y in years for m in months]:
        print 'Inserting:', date
        soup = page_soup('http://www.csidata.com/GetHolidaysForMonth.php?month=%s&year=%s' % (date[1], date[0]))
        with mysql_connection:
            cursor = mysql_connection.cursor()
            cursor.executemany(sql, [values(holiday) for holiday in soup.find_all('holiday')])

if __name__ == '__main__':
    mysql_connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )
    # scrape_holidays()
