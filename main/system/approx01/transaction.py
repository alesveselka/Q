#!/usr/bin/python

from decimal import Decimal


class Transaction(object):

    def __init__(self, transaction_type, account_action, date, amount, currency, notes):
        self.__type = transaction_type
        self.__account_action = account_action
        self.__date = date
        self.__amount = Decimal(amount)  # TODO has it any meaning to convert it here?
        self.__currency = currency
        self.__notes = notes

    def type(self):
        return self.__type

    def account_action(self):
        return self.__account_action

    def date(self):
        return self.__date

    def amount(self):
        return self.__amount

    def currency(self):
        return self.__currency

    def notes(self):
        return self.__notes

    def __str__(self):
        return 'Transaction: %s, %s of %.2f(%s) on %s (%s)' % (
            self.__type,
            self.__account_action,
            self.__amount,
            self.__currency,
            str(self.__date),
            self.__notes
        )
