#!/usr/bin/python

from enum import TransactionType
from collections import defaultdict


class Account(object):

    def __init__(self, initial_balance, base_currency):
        # self.__balance = initial_balance  # Update MTM, Cash, Bonds on new market data
        # self.__base_currency = base_currency

        # self.__securities = [CZK, USD, ...]  # Cash, Commissions, Interest on Credit
        # TODO margin in non-base-currency need to be converted?
        self.__fx_balances = defaultdict(int)  # MTM in Fx until transferred, Interest on Debit (from Margin Loans)
        self.__margin_loan_balances = defaultdict(int)  # Margins
        self.__transactions = [] # (Date, Type(Comm., Interest, Transfer, MTM, ...), Quantity, Cost Price, Currency)

        self.__fx_balances[base_currency] = initial_balance

    def equity(self):
        """
        Calculate and returns actual equity value
        (Sum of all FX balances)

        :return:    Number representing actual equity value
        """
        balance = reduce(lambda t, k: t + self.__fx_balances.get(k), self.__fx_balances.keys(), 0)  # TODO FX conversion!
        return balance

    def available_funds(self):
        """
        Calculates and returns funds available for trading
        (Sum of FX balances minus sum of margin loans)

        :return:    Number representing funds available for trading
        """
        balance = reduce(lambda t, k: t + self.__fx_balances.get(k), self.__fx_balances.keys(), 0)  # TODO FX conversion!
        margin = reduce(lambda t, k: t + self.__margin_loan_balances.get(k), self.__margin_loan_balances.keys(), 0)  # TODO FX conversion!
        return balance - margin

    def take_margin_loan(self, margin, currency):
        """
        Add margin to margin-loan-balances

        :param margin:      Margin amount to be added
        :param currency:    Currency denomination of the margin
        """
        self.__margin_loan_balances[currency] += margin

    def close_margin_loan(self, margin, currency):
        """
        Remove margin from margin-loan_balances

        :param margin:      Margin amount to be subtracted
        :param currency:    Currency denomination of the margin
        """
        self.__margin_loan_balances[currency] -= margin

    def add_transaction(self, transaction):
        """
        Add transaction and update related balances

        :param transaction:     Transaction object to be added
        """
        # self.__fx_balances[transaction.market().currency()] -= transaction.commission()

        self.__transactions.append(transaction)  # TODO modify balances ...

        # previous_transaction = self.__previous_transaction(transaction.market(), transaction.type() ,transaction.date())
        #
        # if previous_transaction:
        #     print transaction, previous_transaction, transaction.price() - previous_transaction.price()
        # else:
        #     print transaction

        # TODO dispatching event instead? (TransactionFilled? ...Complete?)
        return True

    def __previous_transaction(self, market, type, date):
        if type == TransactionType.MTM:
            for t in reversed(self.__transactions):
                if t.market() == market:
                    if t.date() < date and t.type() == TransactionType.MTM:
                        return t
                    elif t.date() == date and (t.type() == TransactionType.BTO or t.type() == TransactionType.STO):
                        return t
        elif type == TransactionType.BTC or type == TransactionType.STC:
            for t in reversed(self.__transactions):
                if t.market() == market:
                    if t.date() < date and t.type() == TransactionType.MTM:
                        return t
                    elif t.date() == date and (t.type() == TransactionType.BTO or t.type() == TransactionType.STO):
                        return t

        return None
