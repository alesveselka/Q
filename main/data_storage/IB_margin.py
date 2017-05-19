#!/usr/bin/python

import bs4
import csv
import requests


def page():
    response = requests.get("https://www.interactivebrokers.com/en/index.php?f=marginnew&p=fut")
    return bs4.BeautifulSoup(response.text, "html.parser")


def exchanges(soup):
    def transform(element):
        items = element.split(' (')
        if len(items) == 1: items.append(items[0].split(' ')[0])
        return [item.replace(')', '') for item in items]
    return [['Name', 'Code']] + [transform(h.text) for h in soup.select('h5')]


def margins(soup):
    ex = exchanges(soup)[1:]
    tables = soup.select('.table-responsive > table')
    header = ['Exchange Name', 'Exchange Code'] + [h.text.replace(' 1', '') for h in tables[0].select('tr > th')][1:]
    table_rows = [t.select('tbody > tr') for t in tables]
    lines = [header]

    for row in table_rows:
        for r in row:
            cells = [cell.text.replace(' 2', '') for cell in r.select('td')]
            ex_code = cells[0].lower()
            ex_name = [e[0] for e in ex if e[1].replace(' ', '').lower() == ex_code][0]
            lines.append([ex_name] + cells)

    return lines


def save_to_file(file_path, lines):
    writer = csv.writer(open(file_path, 'wb'), delimiter=',', quotechar='"')
    writer.writerows(lines)


if __name__ == '__main__':
    dir_path = './resources/IB/'

    # save_to_file(''.join([dir_path, 'IB_exchanges.csv']), exchanges(page()))
    save_to_file(''.join([dir_path, 'IB_margins.csv']), margins(page()))
