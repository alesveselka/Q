#!/usr/bin/python

import bs4
import requests


def page():
    response = requests.get("https://www.interactivebrokers.com/en/index.php?f=marginnew&p=fut")
    return bs4.BeautifulSoup(response.text, "html.parser")


def exchanges(soup):
    def transform(element):
        items = element.split(' (')
        if len(items) == 1: items.append(items[0].split(' ')[0])
        return ','.join(items).replace(')', '')
    return ['Name,Code'] + [transform(h.text) for h in soup.select('h5')]


def margins(soup):
    ex = [e.split(',') for e in exchanges(soup)[1:]]
    tables = soup.select('.table-responsive > table')
    header = ','.join(['Exchange Name', 'Exchange Code'] + [h.text.replace(' 1', '') for h in tables[0].select('tr > th')][1:])
    table_rows = [t.select('tbody > tr') for t in tables]
    lines = [header]

    for row in table_rows:
        for r in row:
            cells = [cell.text.replace(' 2', '') for cell in r.select('td')]
            ex_code = cells[0].lower()
            ex_name = [e[0] for e in ex if e[1].replace(' ', '').lower() == ex_code][0]
            lines.append(','.join([ex_name] + cells))

    return lines


def save_to_file(file_path, lines):
    f = open(file_path, 'w')
    f.write('\n'.join(lines))
    f.close()


if __name__ == '__main__':
    dir_path = './resources/IB/'

    # save_to_file(''.join([dir_path, 'IB_exchanges.csv']), exchanges(page()))
    save_to_file(''.join([dir_path, 'IB_margins.csv']), margins(page()))

    # TODO map IB and Norgate exchanges
    # TODO map IB and Norgate markets
    # TODO insert into DB
    # TODO estimate each margin percentage of price and volatility
