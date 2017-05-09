#!/usr/bin/python

import sys
import datetime as dt
from timer import Timer
from enum import TransactionType
from enum import AccountAction
from enum import Interval
from collections import defaultdict
from decimal import Decimal


class Report:

    def __init__(self, account):
        self.__account = account

    def to_tables(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31), interval=None):
        return self.__formatted_stats(start_date, end_date, interval, self.__table_stats)

    def to_lists(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31), interval=None):

        data = Timer.monthly_date_range(start_date, end_date)
        results = self.__returns(
            [self.__balance_results(end_date=d) for d in data],
            self.__account.initial_balance(),
            self.__account.base_currency()
        )

        for r in results:
            print
            equity_result = [x for x in r if x['title'] == 'Equity'][0]
            equity = equity_result['results'][self.__account.base_currency()]
            print equity, equity_result['return']
            print r

        return self.__formatted_stats(start_date, end_date, interval, self.__list_stats)

    def transactions(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Return list of transactions aggregated daily under the date header

        :param start_date:  start date of the stats
        :param end_date:    end date of the stats
        :return:            list of strings describing transactions aggregated daily
        """
        buffer = ''
        result = []
        date = dt.date(1900, 1, 1)
        transactions = self.__account.transactions(start_date, end_date)
        length = float(len(transactions))
        for i, t in enumerate(transactions):
            self.__log(t.date(), i, length)
            if t.date() > date:
                date = t.date()
                result.append(buffer)
                buffer = (' %s ' % date).center(80, '-') + '\n'
            buffer += str(t) + '\n'
        result.append(buffer)
        self.__log(date, complete=True)
        return result

    def __formatted_stats(self, start_date, end_date, interval, fn):
        """
        Return formatted stats according the style passed in

        :param start_date:  start date of the stats
        :param end_date:    end date of the stats
        :param interval:    time aggregation for the stats
        :param style:       either list or table
        :return:            string representation of the stat in specified style
        """
        if interval == Interval.DAILY:
            data = Timer.daily_date_range(start_date, end_date)
            length = float(len(data))
            result = map(lambda i, : self.__log(i[1], i[0], length) and fn(i[1], i[1]), enumerate(data))
        elif interval == Interval.MONTHLY:
            data = Timer.monthly_date_range(start_date, end_date)
            length = float(len(data))
            result = map(lambda i, : self.__log(i[1], i[0], length) and fn(i[1], dt.date(i[1].year, i[1].month, 1)), enumerate(data))
        elif interval == Interval.YEARLY:
            data = Timer.yearly_date_range(start_date, end_date)
            length = float(len(data))
            result = map(lambda i, : self.__log(i[1], i[0], length) and fn(i[1], dt.date(i[1].year, 1, 1)), enumerate(data))
        else:
            result = [fn(end_date, start_date)]

        self.__log(end_date, complete=True)
        return result

    def __list_stats(self, date, previous_date):
        """
        Compile result list

        :param date:            start date of the stats
        :param previous_date:   end date of the stats
        :return:                string representing the list with results
        """
        balance_results = self.__measure_widths(self.__balance_results(previous_date, date))
        performance_results = self.__measure_widths(self.__performance_results(previous_date, date))
        title_width = max([r['title_width'] for r in performance_results] + [r['title_width'] for r in balance_results]) + 2
        results_width = max([r['results_width'] for r in performance_results] + [r['results_width'] for r in balance_results])
        buffer = self.__to_table_header(previous_date, date, title_width + results_width) + '\n'

        for r in balance_results + performance_results:
            title = r['title']
            for item in r['results'].items():
                buffer += title.ljust(title_width, '.')
                buffer += ('{:-,.2f}'.format(item[1]) + ' ' + item[0] + '\n').rjust(results_width, '.')
                title = ''

        return buffer

    def __table_stats(self, date, previous_date):
        """
        Concat multiple stat tables into one aggregate statistics table

        :param date:            start date of the stats
        :param previous_date:   end date of the stats
        :return:                string representing the full table
        """
        performance_results = self.__measure_widths(self.__performance_results(previous_date, date))
        width = reduce(lambda r, p: r + p['width'], performance_results, 0)
        balance_results = self.__measure_widths(self.__balance_results(previous_date, date), width)
        return '\n'.join([
            self.__to_table_header(previous_date, date, width + len(performance_results) + 1),
            self.__to_table(balance_results),
            self.__to_table(performance_results)
        ])

    def __to_table_header(self, start_date, end_date, width):
        """
        Return table header as a string

        :param start_date:  start date
        :param end_date:    end_date
        :param width:       Width of the header
        :return:            string
        """
        return ''.join([' ', str(start_date), ' - ', str(end_date), ' ']).center(width, '=')

    def __to_table(self, data):
        """
        Construct and return string table from data passed in

        :param data:    dict to render into table
        :return:        string representation of the table
        """
        buffer = ''
        separators = 3
        rows = max([len(d['results']) for d in data])
        table = [[[] for _ in range(0, rows + separators + 1)] for _ in range(len(data))]

        for i, d in enumerate(data):
            w = int(d['width'])

            table[i][0].append('-' * w)
            table[i][1].append((' ' + d['title']).ljust(w, ' '))
            table[i][2].append('-' * w)

            result_items = d['results'].items()
            for row in range(3, rows + separators):
                content = ' ' * w
                if len(result_items) > row - separators:
                    item = result_items[row - separators]
                    content = (' %s: %s' % (item[0], '{:-,.2f}'.format(item[1]))).ljust(w, ' ')
                table[i][row].append(content)

            table[i][rows + separators].append('-' * w)

        for row in range(0, rows + separators + 1):
            line = ['']
            for i, column in enumerate(table):
                line.append(column[row][0])
            buffer += ('+' if row == 0 or row == 2 or row == (rows + separators) else '|').join(line + ['\n'])

        return buffer[:-1]

    def __balance_results(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Partition transactions into map of transaction types and currencies

        :param start_date:  Start date to include transactions from
        :param end_date:    End date to include transactions until
        :return:            dict of dict of performance results
        """
        base_currency = self.__account.base_currency()
        margins = self.__account.margin_loan_balances(end_date)
        total_margin = sum([self.__account.base_value(v, k, end_date) for k, v in margins.items()])
        margin_ratio = {base_currency: total_margin / self.__account.equity(end_date)} if total_margin else {}
        result = [
            {'title': 'Equity', 'results': {base_currency: self.__account.equity(end_date)}},
            {'title': 'Funds', 'results': {base_currency: self.__account.available_funds(end_date)}},
            {'title': 'Balances', 'results': self.__account.fx_balances(end_date)},
            {'title': 'Margins', 'results': margins},
            {'title': 'Margin / Equity', 'results': margin_ratio}
        ]
        return result

    def __performance_results(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Partition transactions into map of transaction types and currencies

        :param start_date:  Start date to include transactions from
        :param end_date:    End date to include transactions until
        :return:            dict of dict of performance results
        """
        types = [
            TransactionType.MTM_POSITION,
            TransactionType.MTM_TRANSACTION,
            TransactionType.COMMISSION,
            TransactionType.FX_BALANCE_TRANSLATION,
            TransactionType.MARGIN_INTEREST,
            TransactionType.BALANCE_INTEREST
        ]
        results = {k: defaultdict(Decimal) for k in types}

        for t in [tr for tr in self.__account.transactions(start_date, end_date) if tr.type() in types]:
            sign = 1 if t.account_action() == AccountAction.CREDIT else -1
            results[t.type()][t.currency()] += t.amount() * sign

        performance_map = [
            {'title': 'Mark-to-Market', 'types': [TransactionType.MTM_POSITION, TransactionType.MTM_TRANSACTION], 'results': defaultdict(Decimal)},
            {'title': 'Commission', 'types': [TransactionType.COMMISSION], 'results': defaultdict(Decimal)},
            {'title': 'Fx Translation', 'types': [TransactionType.FX_BALANCE_TRANSLATION], 'results': defaultdict(Decimal)},
            {'title': 'Interest on Margin', 'types': [TransactionType.MARGIN_INTEREST], 'results': defaultdict(Decimal)},
            {'title': 'Interest on base Balance', 'types': [TransactionType.BALANCE_INTEREST], 'results': defaultdict(Decimal), 'base': True},
            {'title': 'Interest on non-base Balance', 'types': [TransactionType.BALANCE_INTEREST], 'results': defaultdict(Decimal)}
        ]

        base_currency = self.__account.base_currency()
        for p in performance_map:
            for transaction_type in [k for k in results.keys() if k in p['types']]:
                for currency in results[transaction_type].keys():
                    if transaction_type == TransactionType.BALANCE_INTEREST:
                        if p.get('base', False) and currency == base_currency:
                            p['results'][currency] += results[transaction_type][currency]
                        elif not p.get('base', False) and currency != base_currency:
                            p['results'][currency] += results[transaction_type][currency]
                    else:
                        p['results'][currency] += results[transaction_type][currency]

        return performance_map

    def __returns(self, results, initial_balance, base_currency):
        """
        Calculates return on each successive equity balance and add that number to the results structure
         
        :param results:         list of list of dictionaries; 
                                each child list contains result for specified period
        :param initial_balance: initial account balance to start from
        :param base_currency:   currency in which the account is denominated
        :return:                modified 'results' structure with added equity returns
        """
        previous = initial_balance
        for result in [result[0] for result in results if [r for r in result if r['title'] == 'Equity']]:
            equity = result['results'][base_currency]
            result['return'] = equity / previous - 1
            previous = equity
        return results

    def __measure_widths(self, data, min_width=0, prefix=5, pad=1):
        """
        Measure and append table widths to the data passed in

        :param data:        dict which data to measure
        :param min_width:   minimal required width
        :param prefix:      width to prepend to the results' content width
        :param pad:         space to add on both sides of each result content
        :return:            original dict with appended measures data
        """
        total_width = 0
        for d in data:
            values = d['results'].values()
            d['title_width'] = len(d['title'])
            d['results_width'] = max([len('{:-,.2f}'.format(v)) + prefix for v in values]) if len(values) else 0
            d['width'] = max([d['title_width'], d['results_width']]) + pad * 2
            total_width += d['width']

        if total_width < min_width:
            length = len(data)
            addition = (min_width - total_width) / length
            reminder = (min_width - total_width) % length + 1
            for i, d in enumerate(data):
                d['width'] += addition
                d['width'] += reminder if i == length - 1 else 0

        return data

    def __log(self, day, index=0, length=0.0, complete=False):
        """
        Print message and percentage progress to console

        :param index:       Index of the item being processed
        :param length:      Length of the whole range
        :param complete:    Flag indicating if the progress is complete
        """
        sys.stdout.write('%s\r' % (' ' * 80))
        if complete:
            sys.stdout.write('Compiling stats complete\r\n')
        else:
            sys.stdout.write('Compiling stats ... %s (%d of %d) [%s]\r' % (
                day,
                index,
                length,
                '{:.2%}'.format(index / length)
            ))
        sys.stdout.flush()
        return True
