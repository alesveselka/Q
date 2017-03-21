#!/usr/bin/python

from enum import Direction
from enum import OrderType
from enum import TransactionType
from enum import Currency
from transaction import Transaction
from position import Position


class Broker(object):

    def __init__(self, account, portfolio):
        # TODO add settings with commissions, etc.
        self.__account = account
        self.__portfolio = portfolio

    def transfer(self, order):
        commission = 20  # TODO pass-in from config/settings
        margin = order.market().margin(order.price())

        if self.__account.available_funds() > margin + commission:
            self.__account.take_margin_loan(margin, Currency.USD)

            # TODO maybe just pass in Order and let Transaction figure out the parameters?
            transaction = Transaction(order.market(), {
                                          OrderType.BUY: TransactionType.BTO,  # TODO I don't know if it's Buy-to-Open or Buy-to-Close!
                                          OrderType.SELL: TransactionType.STO
                                      }.get(order.type()),
                                      order.date(),
                                      order.price(),  # TODO modify by slippage
                                      order.quantity(),
                                      commission)

            self.__account.add_transaction(transaction)

            # TODO there can be either new position, or closed position! Resolved based on transaction result!
            # TODO maybe just pass in Transaction and let Position figure out the parameters?
            position = Position(transaction.market(), {
                                    TransactionType.BTO: Direction.LONG,
                                    TransactionType.STO: Direction.SHORT
                                }.get(transaction.type()),
                                transaction.date(),
                                transaction.price(),
                                transaction.quantity())

            self.__portfolio.add_position(position)

    def mark_to_market(self):

