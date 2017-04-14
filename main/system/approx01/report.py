#!/usr/bin/python

import sys
import datetime as dt
from enum import TransactionType
from enum import AccountAction
from collections import defaultdict
from decimal import Decimal


class Report:

    def __init__(self, account, orders, trades):
        self.__account = account
        self.__orders = orders
        self.__trades = trades

    def stats(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        # MTM
        # Fx translation
        # Commission
        # Interest on margins
        # interest on non-base balances
        # interest on base balance
        # margin / equity ratio

        date = start_date
        separator = ''.join([('-' * 50), ' %s ', ('-' * 50)])

        # TODO pass in to 'breakdown' yearly, monthly or daily (or all?)
        base_currency = self.__account.base_currency()
        mtm_results = defaultdict(Decimal)
        fx_translations_results = defaultdict(Decimal)
        commissions_results = defaultdict(Decimal)
        margin_interest_results = defaultdict(Decimal)
        base_balance_interest_results = defaultdict(Decimal)
        non_base_balance_interest_results = defaultdict(Decimal)
        for t in self.__account.transactions():
            type = t.type()
            sign = 1 if t.account_action() == AccountAction.CREDIT else -1
            if type == TransactionType.MTM_POSITION or type == TransactionType.MTM_TRANSACTION:
                mtm_results[t.currency()] += t.amount() * sign
            elif type == TransactionType.FX_BALANCE_TRANSLATION:
                fx_translations_results[t.currency()] += t.amount() * sign
            elif type == TransactionType.COMMISSION:
                commissions_results[t.currency()] += t.amount() * sign
            elif type == TransactionType.MARGIN_INTEREST:
                margin_interest_results[t.currency()] += t.amount() * sign
            elif type == TransactionType.BALANCE_INTEREST:
                if t.currency() == base_currency:
                    base_balance_interest_results[t.currency()] += t.amount() * sign
                else:
                    non_base_balance_interest_results[t.currency()] += t.amount() * sign

        trade_profits = defaultdict(Decimal)
        for t in self.__trades:
            market = t.market()
            trade_profits[market.currency()] += t.result() * Decimal(t.quantity()) * market.point_value()

        print 'Equity: %s %s, funds: %.2f %s, balances: %s, margins: %s' % (
            # '{:,}'.format(float(self.__account.equity(end_date))).rjust(20, '.'),
            '{:-,.2f}'.format(float(self.__account.equity(end_date))),
            base_currency,
            self.__account.available_funds(end_date),
            base_currency,
            self.__account.to_fx_balance_string(end_date),
            self.__account.to_margin_loans_string(end_date)
        )
        trade_results = 'Results in %d trades: %s' % (len(self.__trades), {k: float(v) for k, v in trade_profits.items()})
        print trade_results
        print separator % 'results breakdown'
        # print 'Mark-to-Market results:', {k: float(v) for k, v in mtm_results.items()}
        # print 'Fx translation results:', {k: float(v) for k, v in fx_translations_results.items()}
        # print 'Commissions paid:', {k: float(v) for k, v in commissions_results.items()}
        # print 'Interest charged on margins:', {k: float(v) for k, v in margin_interest_results.items()}
        # print 'Interest on balances in non-base currency:', {k: float(v) for k, v in non_base_balance_interest_results.items()}
        # print 'Interest on balances in base currency:', {k: float(v) for k, v in base_balance_interest_results.items()}
        # TODO also slippage!

        performance_results = self.__measure_table(self.__performance_results(start_date, end_date))
        width = reduce(lambda r, p: r + p['width'], performance_results, 0)
        balance_results = self.__measure_table(self.__balance_results(start_date, end_date), width)
        self.__print_balances(balance_results)
        self.__print_performance(performance_results)

        # print self.__balance_results(start_date, end_date)

    def __print_balances(self, balance_map):
        rows = self.__max_results(balance_map)

        table = [[[] for _ in range(0, rows+4)] for _ in range(len(balance_map))]

        for i, balance in enumerate(balance_map):
            w = int(balance['width'])

            table[i][0].append('-' * w)
            table[i][1].append((' ' + balance['title']).ljust(w, ' '))
            table[i][2].append('-' * w)

            result_items = balance['results'].items()

            for row in range(3, rows+3):
                content = ' ' * w
                if len(result_items) > row - 3:
                    item = result_items[row - 3]
                    content = (' %s: %s' % (item[0], '{:-,.2f}'.format(item[1]))).ljust(w, ' ')
                table[i][row].append(content)

            table[i][rows+3].append('-' * w)

        for row in range(0, rows + 4):
            line = ['']
            for i, column in enumerate(table):
                line.append(column[row][0])
            print ('+' if row == 0 or row == 2 or row == (rows + 3) else '|').join(line + [''])

    def __print_performance(self, performance_map):
        rows = self.__max_results(performance_map)

        table = [[[] for _ in range(0, rows+4)] for _ in range(len(performance_map))]

        for i, p in enumerate(performance_map):
            w = int(p['width'])

            table[i][0].append('-' * w)
            table[i][1].append((' ' + p['title']).ljust(w, ' '))
            table[i][2].append('-' * w)

            result_items = p['results'].items()

            for row in range(3, rows+3):
                content = ' ' * w
                if len(result_items) > row - 3:
                    item = result_items[row - 3]
                    content = (' %s: %s' % (item[0], '{:-,.2f}'.format(item[1]))).ljust(w, ' ')
                table[i][row].append(content)

            table[i][rows+3].append('-' * w)

        for row in range(0, rows + 4):
            line = ['']
            for i, column in enumerate(table):
                line.append(column[row][0])
            print ('+' if row == 0 or row == 2 or row == (rows + 3) else '|').join(line + [''])

    def __balance_results(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Partition transactions into map of transaction types and currencies

        :param start_date:  Start date to include transactions from
        :param end_date:    End date to include transactions until
        :return:            dict of dict of performance results
        """
        balances = defaultdict(Decimal)
        for currency in self.__account.fx_balance_currencies():
            balances[currency] += self.__account.fx_balance(currency, end_date)

        margins = defaultdict(Decimal)
        total_margin = Decimal(0)
        for currency in self.__account.margin_loan_currencies():
            margin = self.__account.margin_loan_balance(currency, end_date)
            margins[currency] += margin
            total_margin += self.__account.base_value(margin, currency, end_date)

        base_currency = self.__account.base_currency()
        result = [
            {'title': 'Equity', 'results': {base_currency: self.__account.equity(end_date)}},
            {'title': 'Funds', 'results': {base_currency: self.__account.available_funds(end_date)}},
            {'title': 'Balances', 'results': balances},
            {'title': 'Margins', 'results': margins},
            {'title': 'Margin / Equity', 'results': {base_currency: total_margin / self.__account.equity(end_date)}}
        ]
        # return result
        return [
            {'title': 'Equity', 'results': {'EUR': Decimal(1237151.139124938681955360085)}},
            {'title': 'Funds', 'results': {'EUR': Decimal(1225953.862302661859678537808)}},
            {'title': 'Balances', 'results': {'USD': Decimal(3379.609368248489405560247165), 'EUR': Decimal(1232826.290936660004890505141)}},
            {'title': 'Margins', 'results': {'USD': Decimal(8750)}},
            {'title': 'Margin / Equity', 'results': {'EUR': Decimal(0.009050856009555046173239403523)}}
        ]

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

        # return results

        performance_map = [
            {'title': 'Mark-to-Market', 'types': [TransactionType.MTM_POSITION, TransactionType.MTM_TRANSACTION], 'results': defaultdict(Decimal)},
            {'title': 'Commission', 'types': [TransactionType.COMMISSION], 'results': defaultdict(Decimal)},
            {'title': 'Fx Translation', 'types': [TransactionType.FX_BALANCE_TRANSLATION], 'results': defaultdict(Decimal)},
            {'title': 'Interest on Margin', 'types': [TransactionType.MARGIN_INTEREST], 'results': defaultdict(Decimal)},
            {'title': 'Interest on base Balance', 'types': [TransactionType.BALANCE_INTEREST], 'results': defaultdict(Decimal)},
            {'title': 'Interest on non-base Balance', 'types': [TransactionType.BALANCE_INTEREST], 'results': defaultdict(Decimal)}
        ]

        for p in performance_map:
            for transaction_type in [k for k in results.keys() if k in p['types']]:
                for currency in results[transaction_type].keys():
                    p['results'][currency] += results[transaction_type][currency]

        # return performance_map

        return [
            {'title': 'Mark-to-Market', 'results': {'USD': Decimal(-7375.00000000000000000000)}},
            {'title': 'Commission', 'results': {'USD': Decimal(-100)}},
            {'title': 'Fx Translation', 'results': {}},
            {'title': 'Interest on Margin', 'results': {'USD': Decimal(-9.5385904109589041095890410974)}},
            {'title': 'Interest on base Balance', 'results': {'USD': Decimal(-4.892494623369438184100918898), 'EUR': Decimal(29155.35433443516022309821460)}},
            {'title': 'Interest on non-base Balance', 'results': {'USD': Decimal(-4.892494623369438184100918898), 'EUR': Decimal(29155.35433443516022309821460)}}
        ]

    def __measure_table(self, data, max_width=0, prefix=5, pad=1):
        total_width = 0
        for d in data:
            values = d['results'].values()
            d['title_width'] = len(d['title'])
            d['results_width'] = max([len('{:-,.2f}'.format(v)) + prefix for v in values]) if len(values) else 0
            d['width'] = max([d['title_width'], d['results_width']]) + pad * 2
            total_width += d['width']

        if total_width < max_width:
            length = len(data)
            addition = (max_width - total_width) / length
            reminder = (max_width - total_width) % length + 1
            for i, d in enumerate(data):
                d['width'] += addition
                d['width'] += reminder if i == length - 1 else 0

        return data

    def __max_results(self, data):
        return max([len(d['results']) for d in data])

    def __log(self, day, index=0, length=0.0, complete=False):
        """
        Print message and percentage progress to console

        :param index:       Index of the item being processed
        :param length:      Length of the whole range
        :param complete:    Flag indicating if the progress is complete
        """
        sys.stdout.write('%s\r' % (' ' * 80))
        if complete:
            sys.stdout.write('Strategy progress complete\r\n')
        else:
            sys.stdout.write('Strategy progress ... %s (%d of %d) [%s]\r' % (
                day,
                index,
                length,
                '{.2%}'.format(float(index) / length)
            ))
        sys.stdout.flush()
