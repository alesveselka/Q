#!/usr/bin/python

from enum import Direction
from enum import OrderType
from enum import TransactionType
from transaction import Transaction
from position import Position


class Broker(object):

    def __init__(self, account, portfolio):
        self.__account = account
        self.__portfolio = portfolio

    def transfer(self, order):
        # TODO add commissions
        transaction = Transaction(order.market(), {
                OrderType.BUY: TransactionType.BTO,  # TODO I don't know if it's Buy-to-Open or Buy-to-Close!
                OrderType.SELL: TransactionType.STO
            }.get(order.type()),
            order.date(),
            order.price(),  # TODO modify by slippage
            order.quantity())

        self.__account.add_transaction(transaction)

        # TODO there can be either new position, or closed position! Resolved based on transaction result!
        position = Position(transaction.market(), {
                TransactionType.BTO: Direction.LONG,
                TransactionType.STO: Direction.SHORT
            }.get(transaction.type()),
            transaction.date(),
            transaction.price(),
            transaction.quantity())

        self.__portfolio.add_position(position)
