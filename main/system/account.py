#!/usr/bin/python

import datetime as dt
from enum import TransactionType
from enum import AccountAction
from enum import AccountRecord
from collections import defaultdict
from decimal import Decimal


class Account(object):

    def __init__(self, initial_balance, base_currency, currency_pairs):
        self.__base_currency = base_currency
        self.__currency_pairs = currency_pairs

        self.__fx_balances = defaultdict(Decimal)
        self.__margin_loan_balances = defaultdict(Decimal)
        self.__transactions = []
        self.__records = {}

        self.__fx_balances[base_currency] = initial_balance
        self.__record_balances(dt.date(1900, 1, 1))

    def initial_balance(self):
        """
        Find and return initial equity balance
        
        :return:    Decimal
        """
        return sorted(self.__records.items())[0][1][AccountRecord.EQUITY]

    def base_currency(self):
        """
        Returns account's base currency

        :return:    String representing the base currency symbol
        """
        return self.__base_currency

    def base_value(self, amount, currency, date):
        """
        Return value converted to account-base-currency

        :param amount:      Amount to be converted
        :param currency:    Quote currency in the pair
        :param date:        date on which to convert the amount
        :return:            Converted amount in the account-base-currency
        """
        value = amount
        if currency != self.__base_currency:
            pairs = [cp for cp in self.__currency_pairs if cp.code() == '%s%s' % (self.__base_currency, currency)]
            value = Decimal(amount) / pairs[0].rate(date)
        return value

    def fx_value(self, amount, currency, date):
        """
        Return value converted to account-base-currency

        :param amount:      Amount to be converted
        :param currency:    Quote currency in the pair
        :param date:        date on which to convert the amount
        :return:            Converted amount in the account-base-currency
        """
        value = amount
        if currency != self.__base_currency:
            pairs = [cp for cp in self.__currency_pairs if cp.code() == '%s%s' % (self.__base_currency, currency)]
            value = Decimal(amount) * pairs[0].rate(date)
        return value

    def equity(self, date):
        """
        Returns recorded equity value on the date passed in

        :param date:    date on which return equity value
        :return:        Number representing actual equity value
        """
        return self.__record(date)[AccountRecord.EQUITY]

    def available_funds(self, date):
        """
        Calculates and returns funds available for trading

        :param date:    date on which return equity value
        :return:        Number representing funds available for trading
        """
        record = self.__record(date)
        margin_loans = record[AccountRecord.MARGIN_LOANS]
        return record[AccountRecord.EQUITY] - sum(self.base_value(margin_loans[k], k, date) for k in margin_loans.keys())

    def margin_loan_currencies(self):
        """
        Return list of currencies the account have margin loans

        :return:    List of strings, each representing currency symbol
        """
        return self.__margin_loan_balances.keys()

    def margin_loan_balance(self, currency, date):
        """
        Return margin loan balance for currency Fx passed in

        :param currency:    String representing Fx currency
        :param date:        Date of the final balance
        :return:            Number representing the balance
        """
        margins = self.__record(date)[AccountRecord.MARGIN_LOANS]
        return margins[currency] if currency in margins else Decimal(0)

    def margin_loan_balances(self, date):
        """
        Construct and returns dict of margin loans

        :param date:    date of the balance
        :return:
        """
        return self.__record(date)[AccountRecord.MARGIN_LOANS]

    def fx_balance_currencies(self):
        """
        Return list of currencies the account is holding Fx balances in

        :return:    List of strings, each representing currency symbol
        """
        return self.__fx_balances.keys()

    def fx_balance(self, currency, date):
        """
        Returns balance in currency specified in argument

        :param currency:    String - the currency symbol of requested Fx balance
        :param date:        Date of the final balance
        :return:            Decimal number representing the Fx balance
        """
        balances = self.__record(date)[AccountRecord.FX_BALANCE]
        return balances[currency] if currency in balances else Decimal(0)

    def fx_balances(self, date):
        """
        Construct and returns dict of Fx balances

        :param date:    date of the
        :return:
        """
        return self.__record(date)[AccountRecord.FX_BALANCE]

    def add_transaction(self, transaction):
        """
        Add transaction and update related balances

        :param transaction:     Transaction object to be added
        """
        self.__transactions.append(transaction)

        {AccountAction.CREDIT: self.__credit, AccountAction.DEBIT: self.__debit}[transaction.account_action()](
            {TransactionType.MARGIN_LOAN: self.__margin_loan_balances}.get(transaction.type(), self.__fx_balances),
            transaction.currency(),
            transaction.amount()
        )

        self.__record_balances(transaction.date())

    def transactions(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Find and return transaction within the dates specified (included)

        :param start_date:  Start date to search from
        :param end_date:    End date to search until
        :return:            list of Transaction objects
        """
        return [t for t in self.__transactions if start_date <= t.date() <= end_date]

    def aggregate(self, start_date, end_date, transaction_types):
        """
        Goes through transactions of specified type and within period 
        and aggregate them into currency: amount map
        
        :param start_date:          date when to start aggregation (including)
        :param end_date:            date when to end aggregation (including)
        :param transaction_types:   types of transactions to aggregate
        :return:                    dict(currency: amount)
        """
        result = defaultdict(Decimal)
        for t in [tr for tr in self.transactions(start_date, end_date) if tr.type() in transaction_types]:
            result[t.currency()] += t.amount() * (1 if t.account_action() == AccountAction.CREDIT else -1)
        return result

    def __credit(self, balance, currency, amount):
        """
        Credit specific balance with the amount passed in

        :param balance:     Dictionary of balances
        :param currency:    Currency denomination of the amount to be credited
        :param amount:      Amount to be credited
        """
        balance[currency] += Decimal(amount)

    def __debit(self, balance, currency, amount):
        """
        Debit specific balance with the amount passed in

        :param balance:     Dictionary of balances
        :param currency:    Currency denomination of the amount to be debited
        :param amount:      Amount to be debited
        """
        balance[currency] -= Decimal(amount)

    def __record_balances(self, date):
        """
        Save current values of equity, fx- and margin loan balances

        :param date:    date on which to record
        """
        fx_currencies = self.fx_balance_currencies()
        equity = sum(self.base_value(self.__fx_balances[c], c, date) for c in fx_currencies if self.__fx_balances[c])
        fx_balances = {c: self.__fx_balances[c] for c in fx_currencies if self.__fx_balances[c]}
        margins = {c: self.__margin_loan_balances[c] for c in self.margin_loan_currencies() if self.__margin_loan_balances[c]}

        self.__records[date] = equity, fx_balances, margins

    def __record(self, date):
        """
        Find and return balance record on the date passed in
        
        :param date:    the date of the record
        :return:        tuple (equity, fx balances, margin loans) representing the record on the requested date
        """
        return self.__records[date] if date in self.__records \
            else [r for r in sorted(self.__records.items()) if r[0] <= date][-1][1]
