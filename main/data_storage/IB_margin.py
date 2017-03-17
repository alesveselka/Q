#!/usr/bin/python

import bs4
import requests


def download_page():
    response = requests.get("https://www.interactivebrokers.com/en/index.php?f=marginnew&p=fut")
    return bs4.BeautifulSoup(response.text, "html.parser")


def download_exchanges(soup):
    return ['Name,Code'] + [h.text.replace(' (', ',').replace(')', '') for h in soup.select('h5')]


def download_margins(soup):
    tables = soup.select('.table-responsive > table')
    header = ','.join([h.text.replace(' 1', '') for h in tables[0].select('tr > th')])
    table_rows = [t.select('tbody > tr') for t in tables]
    lines = [header]

    for row in table_rows:
        for r in row:
            lines.append(','.join([cell.text for cell in r.select('td')]))

    return lines


def save_to_file(file_path, lines):
    f = open(file_path, 'w')
    f.write('\n'.join(lines))
    f.close()


if __name__ == '__main__':
    dir_path = './resources/IB/'

    # save_to_file(''.join([dir_path, 'IB_exchanges.csv']), download_exchanges(download_page()))
    save_to_file(''.join([dir_path, 'IB_margins.csv']), download_margins(download_page()))
