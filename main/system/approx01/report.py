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
        # orders = self.__broker.orders()
        # order = None
        # buffer = separator % 'transactions' + '\n'
        # for t in self.__account.transactions():
        #     if t.date() != date:
        #         buffer += ''.join(['Equity: ', str(float(self.__account.equity(date))), ', Funds: ', str(float(self.__account.available_funds(date))),
        #                            ', Balances: ', self.__account.to_fx_balance_string(date), ', Margins: ', self.__account.to_margin_loans_string(date), '\n'])
        #         date = t.date()
        #         buffer += separator % date + '\n'
        #         order = [o for o in orders if o.date() == date]
        #         if len(order):
        #             buffer += str(order[0]) + '\n'
        #     buffer += str(t) + '\n'
        # buffer += ''.join(['Equity: ', str(float(self.__account.equity(date))), ', Funds: ', str(float(self.__account.available_funds(date))),
        #                    ', Balances: ', self.__account.to_fx_balance_string(date), ', Margins: ', self.__account.to_margin_loans_string(date), '\n'])
        #
        # buffer += separator % 'trades' + '\n'

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

        balance_headers = ['Equity', 'Funds', 'Balances', 'Margins', 'Margin / Equity']
        performance_map = [
            {'header': 'Mark-to-Market', 'types': [TransactionType.MTM_POSITION, TransactionType.MTM_TRANSACTION], 'results': defaultdict(Decimal)},
            {'header': 'Commission', 'types': [TransactionType.COMMISSION], 'results': defaultdict(Decimal)},
            {'header': 'Fx Translation', 'types': [TransactionType.FX_BALANCE_TRANSLATION], 'results': defaultdict(Decimal)},
            {'header': 'Interest on Margin', 'types': [TransactionType.MARGIN_INTEREST], 'results': defaultdict(Decimal)},
            {'header': 'Interest on base Balance', 'types': [TransactionType.BALANCE_INTEREST], 'currency': base_currency, 'results': defaultdict(Decimal)},
            {'header': 'Interest on non-base Balance', 'types': [TransactionType.BALANCE_INTEREST], 'results': defaultdict(Decimal)}
        ]

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
        print 'Mark-to-Market results:', {k: float(v) for k, v in mtm_results.items()}
        print 'Fx translation results:', {k: float(v) for k, v in fx_translations_results.items()}
        print 'Commissions paid:', {k: float(v) for k, v in commissions_results.items()}
        print 'Interest charged on margins:', {k: float(v) for k, v in margin_interest_results.items()}
        print 'Interest on balances in non-base currency:', {k: float(v) for k, v in non_base_balance_interest_results.items()}
        print 'Interest on balances in base currency:', {k: float(v) for k, v in base_balance_interest_results.items()}
        # TODO also slippage!

        types = [
            TransactionType.MTM_POSITION,
            TransactionType.MTM_TRANSACTION,
            TransactionType.COMMISSION,
            TransactionType.FX_BALANCE_TRANSLATION,
            TransactionType.MARGIN_INTEREST,
            TransactionType.BALANCE_INTEREST
        ]
        results = self.__partitioned_results(types, start_date, end_date)
        for transaction_type in results.keys():
            for currency in results[transaction_type].keys():
                result = '{:-,.2f}'.format(results[transaction_type][currency])
                print '%s: %s (%s)' % (transaction_type, result, currency)

        prefix = 5
        rows = 0
        for p in performance_map:
            for transaction_type in [k for k in results.keys() if k in p['types']]:
                if len(results[transaction_type]) > rows:
                    rows = len(results[transaction_type])

                for currency in results[transaction_type].keys():
                    p['results'][currency] += results[transaction_type][currency]

                p['header_width'] = len(p['header'])
                p['results_width'] = max([len('{:-,.2f}'.format(v)) + prefix for v in p['results'].values()])
                p['width'] = max([p['header_width'], p['results_width']])

        print '*' * 100

        table = [[[] for _ in range(0, rows+4)] for _ in range(len(performance_map))]

        for i, p in enumerate(performance_map):
            pads = 1
            w = int(p['width']) + pads * 2

            table[i][0].append('-' * w)
            table[i][1].append((' ' + p['header']).ljust(w, ' '))
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

    def __partitioned_results(self, types, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Partition transactions into map of transaction types and currencies

        :param types:       list of transaction types to include in the result map
        :param start_date:  Start date to include transactions from
        :param end_date:    End date to include transactions until
        :return:            dict of dict of performance results
        """
        results = {k: defaultdict(Decimal) for k in types}

        for t in [tr for tr in self.__account.transactions(start_date, end_date) if tr.type() in types]:
            sign = 1 if t.account_action() == AccountAction.CREDIT else -1
            results[t.type()][t.currency()] += t.amount() * sign

        # return results
        return {
            'Fx Balance Translation': {'EUR': Decimal(495.7128667436290545274939486)},
            'Commission': {'USD': Decimal(-1760.0000000000000000000000000)},
            'Balance Interest': {'USD': Decimal(-28.60076056902745059268604813), 'EUR': Decimal(225088.9819162945147743464073)},
            'Margin Interest': {'USD': Decimal(-876.4234649315068493150684923)},
            'MTM Position': {'USD': Decimal(28537.5000000000000000000000000)},
            'MTM Transaction': {'USD': Decimal(-19381.25000000000000000000000000)}
        }

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
