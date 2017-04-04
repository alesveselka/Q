#!/usr/bin/python

from enum import TransactionType
from enum import AccountAction
from collections import defaultdict
from decimal import Decimal


class Account(object):

    def __init__(self, initial_balance, base_currency, investment_universe):
        # self.__balance = initial_balance  # Update MTM, Cash, Bonds on new market data
        self.__base_currency = base_currency
        self.__investment_universe = investment_universe  # TODO don't need it - just currency pairs

        # self.__securities = [CZK, USD, ...]  # Cash, Commissions, Interest on Credit
        self.__fx_balances = defaultdict(Decimal)  # MTM in Fx until transferred, Interest on Debit (from Margin Loans)
        self.__margin_loan_balances = defaultdict(Decimal)  # Margins
        self.__transactions = []

        self.__fx_balances[base_currency] = initial_balance

    def base_currency(self):
        """
        Returns account's base currency

        :return:    String representing the base currency symbol
        """
        return self.__base_currency

    def base_value(self, amount, currency):
        """
        Return value converted to account-base-currency

        :param amount:      Amount to be converted
        :param currency:    Quote currency in the pair
        :return:            Converted amount in the account-base-currency
        """
        pair = self.__investment_universe.currency_pair('%s%s' % (self.__base_currency, currency))
        # TODO use specific date, not just last day in data!
        # TODO remove hard-coded values
        rate = pair[0].data()[-1][4] if len(pair) else Decimal(1)
        return Decimal(amount) / rate

    def equity(self):
        """
        Calculate and returns actual equity value
        (Sum of all FX balances)

        :return:    Number representing actual equity value
        """
        balance = reduce(lambda t, k: t + self.base_value(self.__fx_balances.get(k), k), self.__fx_balances.keys(), Decimal(0))
        return balance

    def available_funds(self):
        """
        Calculates and returns funds available for trading
        (Sum of FX balances minus sum of margin loans)

        :return:    Number representing funds available for trading
        """
        balance = reduce(lambda t, k: t + self.base_value(self.__fx_balances.get(k), k), self.__fx_balances.keys(), 0)
        margin = reduce(lambda t, k: t + self.base_value(self.__margin_loan_balances.get(k), k), self.__margin_loan_balances.keys(), 0)
        return balance - margin

    def margin_loan_currencies(self):
        """
        Return list of currencies the account have margin loans

        :return:    List of strings, each representing currency symbol
        """
        return self.__margin_loan_balances.keys()

    def margin_loan_balance(self, currency, date=None):
        """
        Return margin loan balance for currency Fx passed in

        :param currency:    String representing Fx currency
        :param date:        Date of the final balance
        :return:            Number representing the balance
        """
        return self.__balance_to_date(
            self.__margin_loan_balances[currency],
            date,
            lambda t: t.type() == TransactionType.MARGIN_LOAN and t.currency() == currency
        )

    def fx_balance_currencies(self):
        """
        Return list of currencies the account is holding Fx balances in

        :return:    List of strings, each representing currency symbol
        """
        return self.__fx_balances.keys()

    def fx_balance(self, currency, date=None):
        """
        Returns balance in currency specified in argument

        :param currency:    String - the currency symbol of requested Fx balance
        :param date:        Date of the final balance
        :return:            Number representing the Fx balance
        """
        return self.__balance_to_date(
            self.__fx_balances[currency],
            date,
            lambda t: t.type() != TransactionType.MARGIN_LOAN and t.currency() == currency
        )

    def to_fx_balance_string(self):
        """
        Return string representation of the Fx balances

        :return:    String representing the account's Fx balances
        """
        return '{%s}' % ', '.join(['%s: %.2f' % (b[0], float(b[1])) for b in self.__fx_balances.items() if b[1]])

    def to_margin_loans_string(self):
        """
        Return string representation of the margin loan balances

        :return:    String representing the account's margin loan balances
        """
        return '{%s}' % ', '.join(['%s: %.2f' % (b[0], float(b[1])) for b in self.__margin_loan_balances.items() if b[1]])

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

    def __credit(self, balance, currency, amount):
        """
        Credit specific balance with the amount passed in

        :param balance:     Dictionary of balances
        :param currency:    Currency denomination of the amount to be credited
        :param amount:      Amount to be credited
        """
        balance[currency] += amount

    def __debit(self, balance, currency, amount):
        """
        Debit specific balance with the amount passed in

        :param balance:     Dictionary of balances
        :param currency:    Currency denomination of the amount to be debited
        :param amount:      Amount to be debited
        """
        balance[currency] -= amount

    def __balance_to_date(self, balance, date, predicate):
        """
        Calculate balance to the date passed in

        :param balance:     Number - starting balance
        :param date:        Date of the final balance
        :param predicate:   Function predicate - condition to meet to include a transaction
        :return:            Number representing the final balance
        """
        if date:
            for t in reversed(self.__transactions):
                if t.date() > date:
                    if predicate(t):
                        if t.account_action() == AccountAction.CREDIT:
                            balance -= t.amount()
                        elif t.account_action() == AccountAction.DEBIT:
                            balance += t.amount()
                else:
                    break

        return balance
