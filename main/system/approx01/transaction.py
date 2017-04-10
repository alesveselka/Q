#!/usr/bin/python

from decimal import Decimal
from enum import TransactionType
from enum import AccountAction


class Transaction(object):

    def __init__(self, transaction_type, account_action, date, amount, currency, context_data=None):
        self.__type = transaction_type
        self.__account_action = account_action
        self.__date = date
        self.__amount = Decimal(amount)  # TODO has it any meaning to convert it here?
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

    # def notes(self):
    #     return self.__notes

    def __str__(self):
        if self.__type == TransactionType.MTM_POSITION:
            return 'Transaction: MTM %.2f(%s) at %.4f' % (self.__amount, self.__currency, self.__context_data)
        elif self.__type == TransactionType.MTM_TRANSACTION:
            return 'Transaction: MTM %.2f(%s) at %.4f' % (self.__amount, self.__currency, self.__context_data)
        elif self.__type == TransactionType.COMMISSION:
            market = self.__context_data[0]
            order = self.__context_data[1]
            return 'Transaction: %s %d x %s at %.2f' % (order.type(), order.quantity(), market.code(), self.__context_data[2])
        elif self.__type == TransactionType.MARGIN_LOAN:
            if self.__account_action == AccountAction.CREDIT:
                return 'Transaction: Take %.2f(%s) margin loan (ADD)' % (self.__amount, self.__currency)
            elif self.__account_action == AccountAction.DEBIT:
                return 'Transaction: Close %.2f(%s) margin loan (REMOVE)' % (self.__amount, self.__currency)
            # Margin Loan
            # 'Close %.2f(%s) margin loan (REMOVE)' % (margin, market.currency())
            # 'Take %.2f(%s) margin loan (ADD)' % (margin, market.currency())
            # 'Close %.2f(%s) margin loan (UPDATE)' % (float(margin_loans_to_close[currency]), currency)
            # 'Take %.2f(%s) margin loan (UPDATE)' % (float(margin_loans_to_open[currency]), currency)
        elif self.__type == TransactionType.INTERNAL_FUND_TRANSFER:
            if self.__account_action == AccountAction.CREDIT:
                return 'Transaction: Transfer funds, %s of %.4f %s to %s balance' % (
                    self.__account_action,
                    self.__amount,
                    self.__currency,
                    self.__currency
                )
            elif self.__account_action == AccountAction.DEBIT:
                return 'Transaction: Transfer funds, %s of %.4f %s from %s balance' % (
                    self.__account_action,
                    self.__amount,
                    self.__currency,
                    self.__currency
                )
        elif self.__type == TransactionType.FX_BALANCE_TRANSLATION:
            return 'Transaction: FX Translation %.2f(%s) of %.2f(%s), rate: %.4f, prior: %.4f' % (
                self.__amount,
                self.__currency,
                self.__context_data[0],
                self.__context_data[1],
                self.__context_data[2],
                self.__context_data[3]
            )
        elif self.__type == TransactionType.INTEREST_CHARGED:
            return 'Transaction: %s Charge %.2f(%s) interest on %.2f %s %s' % (
                self.__account_action,
                self.__amount,
                self.__currency,
                self.__context_data[0],
                self.__currency,
                self.__context_data[3]
            )
        elif self.__type == TransactionType.INTEREST_PAID:
            return 'Transaction: Pay %.2f(%s) interest (@ %.4f) on %.2f(%s) balance' % (
                self.__amount,
                self.__currency,
                self.__context_data[3],
                self.__context_data[0] - self.__context_data[1],
                self.__currency
            )

        # return 'Transaction: %s, %s of %.2f(%s) on %s (%s)' % (
        #     self.__type,
        #     self.__account_action,
        #     self.__amount,
        #     self.__currency,
        #     str(self.__date),
        #     self.__notes
        # )
