#!/usr/bin/python

from enum import Currency
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
        balance = reduce(lambda t, b: t + b, self.__fx_balances, 0)  # TODO FX conversion!
        return balance

    def available_funds(self):
        """
        Calculates and returns funds available for trading
        (Sum of FX balances minus sum of margin loans)

        :return:    Number representing funds available for trading
        """
        balance = reduce(lambda t, b: t + b, self.__fx_balances, 0)  # TODO FX conversion!
        margin = reduce(lambda t, b: t + b, self.__margin_loan_balances, 0)  # TODO FX conversion!
        return balance - margin

    def take_margin_loan(self, margin, currency):
        self.__margin_loan_balances[currency] += margin

    def add_transaction(self, transaction):
        self.__fx_balances[transaction.market().currency()] -= transaction.commission()

        self.__transactions.append(transaction)  # TODO modify balances ...

        # TODO dispatching event instead? (TransactionFilled? ...Complete?)
        return True
