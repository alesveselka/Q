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
from collections import defaultdict
from decimal import Decimal


class Broker(object):

    def __init__(self, account, portfolio, commission, investment_universe, interest_rates):
        self.__account = account
        self.__portfolio = portfolio
        self.__commission = commission
        self.__investment_universe = investment_universe
        self.__interest_rates = interest_rates
        self.__orders = []

    def transfer(self, order, margin):
        market = order.market()
        slippage = Decimal(market.slippage(order.market_volume(), order.market_atr()))
        commission = self.__commission * order.quantity()
        price = (order.price() + slippage) if (order.type() == OrderType.BTO or order.type() == OrderType.BTC) else (order.price() - slippage)  # TODO pass in slippage separe?
        positions_in_market = self.__portfolio.positions_in_market(market)

        if len(positions_in_market):
            # -to-close transactions TODO do I need this check? The orders already know this!

            position = positions_in_market[0]  # TODO what if there is more than one position?
            mtm = position.mark_to_market(order.date(), price) * Decimal(position.quantity()) * market.point_value()
            transaction3 = Transaction(
                TransactionType.MTM_TRANSACTION,
                AccountAction.CREDIT if mtm > 0 else AccountAction.DEBIT,
                order.date(),
                abs(mtm),
                market.currency(),
                'MTM %.2f(%s) at %.2f' % (float(mtm), market.currency(), price)
            )

            self.__account.add_transaction(transaction3)

            print transaction3, float(self.__account.equity()), float(self.__account.available_funds())

            transaction1 = Transaction(
                TransactionType.COMMISSION,
                AccountAction.DEBIT,
                order.date(),
                commission,
                market.currency(),  # TODO market's currency is not necessarily commission's currency
                '%s %d x %s at %.2f' % (order.type(), order.quantity(), market.code(), price)
            )

            self.__account.add_transaction(transaction1)

            print transaction1, float(self.__account.equity()), float(self.__account.available_funds())

            transaction2 = Transaction(
                TransactionType.MARGIN_LOAN,
                AccountAction.DEBIT,
                order.date(),
                margin,
                market.currency(),
                'Close %.2f(%s) margin loan' % (margin, market.currency())
            )

            self.__account.add_transaction(transaction2)

            print transaction2, float(self.__account.equity()), float(self.__account.available_funds())

            self.__portfolio.remove_position(position)
        else:
            # -to-open transactions
            if self.__account.available_funds() > self.__account.base_value(margin + commission, market.currency()):

                transaction1 = Transaction(
                    TransactionType.MARGIN_LOAN,
                    AccountAction.CREDIT,
                    order.date(),
                    margin,
                    market.currency(),
                    'Take %.2f(%s) margin loan' % (margin, market.currency())
                )

                self.__account.add_transaction(transaction1)

                print transaction1, float(self.__account.equity()), float(self.__account.available_funds())

                transaction2 = Transaction(
                    TransactionType.COMMISSION,
                    AccountAction.DEBIT,
                    order.date(),
                    commission,
                    market.currency(),  # TODO market's currency is not necessarily commission's currency
                    '%s %d x %s at %.2f' % (order.type(), order.quantity(), market.code(), price)
                )

                self.__account.add_transaction(transaction2)

                print transaction2, float(self.__account.equity()), float(self.__account.available_funds())

                position = Position(market, {
                        OrderType.BTO: Direction.LONG,
                        OrderType.STO: Direction.SHORT
                    }.get(order.type()),
                    order.date(),
                    order.price(),
                    price,
                    order.quantity())

                self.__portfolio.add_position(position)

        return OrderResult(OrderResultType.FILLED, order.date(), price, commission)

    def mark_to_market(self, date):
        for p in self.__portfolio.positions():
            market = p.market()
            price = market.data(date, date)[-1][5]
            mtm = p.mark_to_market(date, price) * Decimal(p.quantity()) * p.market().point_value()
            transaction = Transaction(
                TransactionType.MTM_TRANSACTION if p.date() == date else TransactionType.MTM_POSITION,
                AccountAction.CREDIT if mtm > 0 else AccountAction.DEBIT,
                date,
                abs(mtm),
                market.currency(),
                'MTM %.2f(%s) at %.2f' % (float(mtm), market.currency(), price)
            )

            self.__account.add_transaction(transaction)

            print transaction, float(self.__account.equity()), float(self.__account.available_funds())

    def translate_fx_balances(self, date, previous_day):
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            pair = self.__investment_universe.currency_pair('%s%s' % (base_currency, currency))
            # TODO remove hard-coded values
            rate = pair[0].data(end_date=date)[-1][4] if len(pair) else Decimal(1)
            prior_rate = pair[0].data(end_date=date)[-2][4] if len(pair) else rate
            rate_difference = rate - prior_rate
            balance = self.__account.fx_balance(currency, previous_day)
            translation = balance * rate_difference

            if balance:
                transaction = Transaction(
                    TransactionType.FX_BALANCE_TRANSLATION,
                    AccountAction.CREDIT if translation > 0 else AccountAction.DEBIT,
                    date,
                    abs(translation),
                    base_currency,
                    'FX Translation %.2f(%s) of %.2f(%s), prior: %.2f, current: %.2f' % (float(translation), base_currency, balance, currency, prior_rate, rate)
                )

                self.__account.add_transaction(transaction)

                print transaction, float(self.__account.equity()), float(self.__account.available_funds())

    def update_margin_loans(self, date, price):
        if len(self.__portfolio.positions()):
            margin_loans = defaultdict(Decimal)

            for p in self.__portfolio.positions():
                market = p.market()
                margin_loans[market.currency()] += Decimal(market.margin(price))

            for currency in margin_loans.keys():
                debit_transaction = Transaction(
                    TransactionType.MARGIN_LOAN,
                    AccountAction.DEBIT,
                    date,
                    self.__account.margin_loan_balance(currency),
                    currency,
                    'Close %.2f(%s) margin loan' % (self.__account.margin_loan_balance(currency), currency)
                )
                self.__account.add_transaction(debit_transaction)

                print debit_transaction, float(self.__account.equity()), float(self.__account.available_funds())

                credit_transaction = Transaction(
                    TransactionType.MARGIN_LOAN,
                    AccountAction.CREDIT,
                    date,
                    margin_loans[currency],
                    currency,
                    'Take %.2f(%s) margin loan' % (float(margin_loans[currency]), currency)
                )
                self.__account.add_transaction(credit_transaction)

                print credit_transaction, float(self.__account.equity()), float(self.__account.available_funds())

    def charge_interest(self, date, previous_date):
        """
        Charge interest on margin loan balances

        :param date:            Date of the charge
        :param previous_date:   Date of interest calculation (previous date for overnight margins)
        """
        # charge interest on debit margin balances
        # pay interest on credit balances
        # TODO add/subtract spread to the BM (benchmark interest)
        days = 365
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.margin_loan_currencies() if c != base_currency]:
            spread = Decimal(2.0)
            benchmark_interest = [r for r in self.__interest_rates if r.code() == currency][0]
            rate = (benchmark_interest.immediate_rate(previous_date) + spread) / 100
            balance = self.__account.margin_loan_balance(currency, previous_date)

            if balance:
                amount = balance * rate / days

                transaction = Transaction(
                    TransactionType.INTEREST,
                    AccountAction.DEBIT,
                    date,
                    amount,
                    currency,
                    'Charge %.2f(%s) interest on %.2f margin' % (amount, currency, balance)
                )
                self.__account.add_transaction(transaction)

                print transaction, float(self.__account.equity()), float(self.__account.available_funds())
