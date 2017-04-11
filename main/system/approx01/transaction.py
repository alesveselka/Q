#!/usr/bin/python

from enum import TransactionType
from enum import AccountAction


class Transaction(object):

    def __init__(self, transaction_type, date, amount, currency, context_data=None):
        self.__type = transaction_type
        self.__account_action = AccountAction.CREDIT if amount > 0 else AccountAction.DEBIT
        self.__date = date
        self.__amount = abs(amount)
        self.__currency = currency
        self.__context_data = context_data

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

    def __str__(self):
        result = 'Transaction: '
        if self.__type == TransactionType.MTM_TRANSACTION or self.__type == TransactionType.MTM_POSITION:
            result += '%s, %s of %.2f(%s) at %.4f (%s).' % (
                self.__type,
                self.__account_action,
                self.__amount,
                self.__currency,
                self.__context_data[1],
                self.__context_data[0].code()
            )
        elif self.__type == TransactionType.COMMISSION:
            market = self.__context_data[0]
            order = self.__context_data[1]
            result += '%s, %s of %.2f(%s): %s %d x %s at %.2f.' % (
                self.__type,
                self.__account_action,
                self.__amount,
                self.__currency,
                order.type(),
                order.quantity(),
                market.code(),
                self.__context_data[2]
            )
        elif self.__type == TransactionType.MARGIN_LOAN:
            result += '%s Margin Loan, %s of %.2f(%s) (%s).' % (
                'Take' if self.__account_action == AccountAction.CREDIT else 'Close',
                self.__account_action,
                self.__amount,
                self.__currency,
                self.__context_data
            )
        elif self.__type == TransactionType.INTERNAL_FUND_TRANSFER:
            result += 'Transfer funds, %s of %.4f(%s) %s %s balance.' % (
                self.__account_action,
                self.__amount,
                self.__currency,
                'to' if self.__account_action == AccountAction.CREDIT else 'from',
                self.__currency
            )
        elif self.__type == TransactionType.FX_BALANCE_TRANSLATION:
            result += 'FX Translation, %s of %.2f(%s) on %.2f(%s) balance, rate: %.4f, prior: %.4f.' % (
                self.__account_action,
                self.__amount,
                self.__currency,
                self.__context_data[0],
                self.__context_data[1],
                self.__context_data[2],
                self.__context_data[3]
            )
        elif self.__type == TransactionType.INTEREST:
            result += 'Interest, %s of %.2f(%s @ %.2f %%) on %.2f(%s) %s.' % (
                self.__account_action,
                self.__amount,
                self.__currency,
                self.__context_data[2] * 100,
                self.__context_data[0],
                self.__currency,
                self.__context_data[3]
            )

        return result
