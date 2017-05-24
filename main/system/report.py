#!/usr/bin/python

import sys
import datetime as dt
from timer import Timer
from enum import TransactionType
from enum import Interval


class Report:

    def __init__(self, account):
        self.__account = account

    def to_lists(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31), interval=None):
        balance_results, performance_results = self.__results(start_date, end_date, interval)
        return [self.__list_stats(balance_results[i], performance_results[i]) for i in range(0, len(balance_results))]

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

    def __list_stats(self, balance_results, performance_results):
        """
        Compile result list

        :param balance_results:     list of balance results
        :param performance_results: list of performance results
        :return:                    string representing the list with results
        """
        meta = [r for r in balance_results if r['title'] == 'Meta'][0]
        balance_results = self.__measure_widths([r for r in balance_results if r['title'] != 'Meta'])
        performance_results = self.__measure_widths(performance_results)
        title_width = max([r['title_width'] for r in performance_results] + [r['title_width'] for r in balance_results]) + 2
        results_width = max([r['results_width'] for r in performance_results] + [r['results_width'] for r in balance_results])
        buffer = self.__header(meta['start_date'], meta['end_date'], title_width + results_width) + '\n'

        for r in balance_results + performance_results:
            title = r['title']
            for item in r['results'].items():
                buffer += title.ljust(title_width, '.')
                ret = ' {:.3%}'.format(r['return']) if 'return' in r else ''
                buffer += ('{:-,.2f}'.format(item[1]) + ' ' + item[0] + ret + '\n').rjust(results_width, '.')
                title = ''

        return buffer

    def __header(self, start_date, end_date, width):
        """
        Return table header as a string

        :param start_date:  start date
        :param end_date:    end_date
        :param width:       Width of the header
        :return:            string
        """
        return ''.join([' ', str(start_date), ' - ', str(end_date), ' ']).center(width, '=')

    def __results(self, start_date, end_date, interval):
        """
        Assembles balance and performance results and return resulting lists
        
        :param start_date:  start date
        :param end_date:    end date
        :param interval:    interval constant
        :return:            tuple(balance results list, performance results list)
        """
        balance_results = []
        performance_results = []
        data = {
            Interval.DAILY: Timer.daily_date_range(start_date, end_date),
            Interval.MONTHLY: Timer.monthly_date_range(start_date, end_date),
            Interval.YEARLY: Timer.yearly_date_range(start_date, end_date)
        }.get(interval, [])
        length = float(len(data))

        if length:
            for i, d in enumerate(data):
                self.__log(d, i, length)
                balance_results += [self.__balance_results(self.__previous_date(d, interval), d)]
                performance_results += [self.__performance_results(self.__previous_date(d, interval), d)]
        else:
            balance_results += [self.__balance_results(start_date, end_date)]
            performance_results += [self.__performance_results(start_date, end_date)]

        self.__log(end_date, complete=True)

        return (
            self.__returns(balance_results, self.__account.initial_balance(), self.__account.base_currency()),
            performance_results
        )

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
            {'title': 'Meta', 'start_date': start_date, 'end_date': end_date},
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
        fn = self.__account.aggregate
        base_currency = self.__account.base_currency()
        balance_interest = fn(start_date, end_date, [TransactionType.BALANCE_INTEREST])
        return [
            {'title': 'Mark-to-Market', 'results': fn(start_date, end_date, [TransactionType.MTM_TRANSACTION, TransactionType.MTM_POSITION])},
            {'title': 'Commission', 'results': fn(start_date, end_date, [TransactionType.COMMISSION])},
            {'title': 'Fx Translation', 'results': fn(start_date, end_date, [TransactionType.FX_BALANCE_TRANSLATION])},
            {'title': 'Interest on Margin', 'results': fn(start_date, end_date, [TransactionType.MARGIN_INTEREST])},
            {'title': 'Interest on base Balance', 'results': {k: v for k, v in balance_interest.items() if k == base_currency}},
            {'title': 'Interest on non-base Balance', 'results': {k: v for k, v in balance_interest.items() if k != base_currency}}
        ]

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
        for result in [[r for r in result if r['title'] == 'Equity'][0] for result in results]:
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

    def __previous_date(self, date, interval):
        """
        Return new date based on interval constant passed in
        :param date:        date to derive new date from
        :param interval:    constant to use for derivation
        :return:            date
        """
        return {
            Interval.MONTHLY: dt.date(date.year, date.month, 1),
            Interval.YEARLY: dt.date(date.year, 1, 1)
        }.get(interval, date)

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
