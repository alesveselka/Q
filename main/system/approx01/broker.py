#!/usr/bin/python

from enum import Direction
from enum import OrderType
from enum import OrderResultType
from enum import TransactionType
from enum import AccountAction
from enum import Currency
from transaction import Transaction
from position import Position
from order_result import OrderResult
from decimal import Decimal


class Broker(object):

    def __init__(self, account, portfolio, commission):
        self.__account = account
        self.__portfolio = portfolio
        self.__commission = commission
        self.__orders = []

    def transfer(self, order):
        market = order.market()
        margin = market.margin(order.price())
        slippage = Decimal(market.slippage(order.market_volume(), order.market_atr()))
        commission = self.__commission * order.quantity()
        price = (order.price() + slippage) if (order.type() == OrderType.BTO or order.type() == OrderType.BTC) else order.price() - slippage  # TODO pass in slippage separe?
        positions_in_market = self.__portfolio.positions_in_market(market)

        if len(positions_in_market):
            # -to-close transactions

            transaction1 = Transaction(
                TransactionType.COMMISSION,
                AccountAction.DEBIT,
                order.date(),
                commission,
                market.currency(),
                '%s %d x %s' % (order.type(), order.quantity(), market.code())
            )

            self.__account.add_transaction(transaction1)

            transaction2 = Transaction(
                TransactionType.MARGIN_LOAN,
                AccountAction.DEBIT,
                order.date(),
                margin,  # TODO make sure the margin actually match!
                market.currency(),
                'Close %.2f(%s) margin loan' % (margin, market.currency())
            )

            self.__account.add_transaction(transaction2)

            position = positions_in_market[0]
            mtm = position.mark_to_market(order.date(), price) * market.point_value()
            transaction3 = Transaction(
                TransactionType.MTM_POSITION,
                AccountAction.CREDIT if mtm > 0 else AccountAction.DEBIT,
                order.date(),
                mtm,
                market.currency(),
                'MTM %.2f(%s) at %.2f' % (mtm, market.currency(), price)
            )

            self.__account.add_transaction(transaction3)

            print transaction1
            print transaction2
            print transaction3

            # self.__account.close_margin_loan(margin, Currency.USD)

            # TODO what if there is more than one position?

            self.__portfolio.remove_position(position)
        else:
            # -to-open transactions
            if self.__account.available_funds() > margin + commission:
                # self.__account.take_margin_loan(margin, Currency.USD)

                transaction1 = Transaction(
                    TransactionType.MARGIN_LOAN,
                    AccountAction.CREDIT,
                    order.date(),
                    margin,
                    market.currency(),
                    'Take %.2f(%s) margin loan' % (margin, market.currency())
                )

                self.__account.add_transaction(transaction1)

                transaction2 = Transaction(
                    TransactionType.COMMISSION,
                    AccountAction.DEBIT,
                    order.date(),
                    commission,
                    market.currency(),
                    '%s %d x %s' % (order.type(), order.quantity(), market.code())
                )

                self.__account.add_transaction(transaction2)

                print transaction1
                print transaction2

                # TODO maybe just pass in Transaction and let Position figure out the parameters?
                position = Position(market, {
                                        OrderType.BTO: Direction.LONG,
                                        OrderType.STO: Direction.SHORT
                                    }.get(order.type()),
                                    order.date(),
                                    price,
                                    order.quantity())

                self.__portfolio.add_position(position)

        return OrderResult(OrderResultType.FILLED, order.date(), price)
