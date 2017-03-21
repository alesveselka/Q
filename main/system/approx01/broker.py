#!/usr/bin/python

from enum import Direction
from enum import OrderType
from enum import TransactionType
from enum import Currency
from enum import Study
from transaction import Transaction
from position import Position
from study import ATR
from study import SMA
from decimal import Decimal


class Broker(object):

    def __init__(self, account, portfolio, commission):
        self.__account = account
        self.__portfolio = portfolio
        self.__commission = commission

    def transfer(self, order):
        market = order.market()
        margin = market.margin(order.price())
        slippage = Decimal(market.slippage(order.market_volume(), order.market_atr()))
        commission = self.__commission * order.quantity()
        price = (order.price() + slippage) if order.type() == OrderType.BUY else order.price() - slippage  # TODO pass in slippage separe?
        positions_in_market = self.__portfolio.positions_in_market(market)

        if len(positions_in_market):
            # -to-close transactions
            transaction = Transaction(market, {
                                          OrderType.BUY: TransactionType.BTC,
                                          OrderType.SELL: TransactionType.STC
                                      }.get(order.type()),
                                      order.date(),
                                      price,
                                      order.quantity(),
                                      commission)

            self.__account.add_transaction(transaction)
            self.__account.close_margin_loan(margin, Currency.USD)

            self.__portfolio.remove_position(positions_in_market[0])  # TODO what if there is ore than one position?
        else:
            # -to-open transactions
            if self.__account.available_funds() > margin + commission:
                self.__account.take_margin_loan(margin, Currency.USD)

                transaction = Transaction(market, {
                                              OrderType.BUY: TransactionType.BTO,
                                              OrderType.SELL: TransactionType.STO
                                          }.get(order.type()),
                                          order.date(),
                                          price,
                                          order.quantity(),
                                          commission)

                self.__account.add_transaction(transaction)

                # TODO maybe just pass in Transaction and let Position figure out the parameters?
                position = Position(transaction.market(), {
                                        TransactionType.BTO: Direction.LONG,
                                        TransactionType.STO: Direction.SHORT
                                    }.get(transaction.type()),
                                    transaction.date(),
                                    transaction.price(),
                                    transaction.quantity())

                self.__portfolio.add_position(position)
