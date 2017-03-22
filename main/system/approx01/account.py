#!/usr/bin/python

from enum import TransactionType
from enum import AccountAction
from collections import defaultdict
from decimal import Decimal


class Account(object):

    def __init__(self, initial_balance, base_currency):
        # self.__balance = initial_balance  # Update MTM, Cash, Bonds on new market data
        # self.__base_currency = base_currency

        # self.__securities = [CZK, USD, ...]  # Cash, Commissions, Interest on Credit
        # TODO margin in non-base-currency need to be converted?
        self.__fx_balances = defaultdict(Decimal)  # MTM in Fx until transferred, Interest on Debit (from Margin Loans)
        self.__margin_loan_balances = defaultdict(Decimal)  # Margins
        self.__transactions = [] # (Date, Type(Comm., Interest, Transfer, MTM, ...), Quantity, Cost Price, Currency)

        self.__fx_balances[base_currency] = initial_balance

    def equity(self):
        """
        Calculate and returns actual equity value
        (Sum of all FX balances)

        :return:    Number representing actual equity value
        """
        balance = reduce(lambda t, k: t + self.__fx_balances.get(k), self.__fx_balances.keys(), Decimal(0))  # TODO FX conversion!
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
        self.__transactions.append(transaction)

        if transaction.type() == TransactionType.MARGIN_LOAN:
            if transaction.account_action() == AccountAction.CREDIT:
                self.__margin_loan_balances[transaction.currency()] += transaction.amount()
            elif transaction.account_action() == AccountAction.DEBIT:
                self.__margin_loan_balances[transaction.currency()] -= transaction.amount()
        else:
            if transaction.account_action() == AccountAction.CREDIT:
                self.__fx_balances[transaction.currency()] += transaction.amount()
            elif transaction.account_action() == AccountAction.DEBIT:
                self.__fx_balances[transaction.currency()] -= transaction.amount()
