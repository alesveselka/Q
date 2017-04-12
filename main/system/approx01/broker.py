#!/usr/bin/python

from enum import Direction
from enum import OrderType
from enum import OrderResultType
from enum import TransactionType
from enum import AccountAction
from enum import EventType
from transaction import Transaction
from position import Position
from order_result import OrderResult
from collections import defaultdict
from decimal import Decimal


class Broker(object):

    def __init__(self, timer, account, portfolio, commission, currency_pairs, interest_rates):
        self.__timer = timer
        self.__account = account
        self.__portfolio = portfolio
        self.__commission = commission
        self.__currency_pairs = currency_pairs
        self.__interest_rates = interest_rates
        self.__orders = []  # TODO save orders!

    def subscribe(self):
        """
        Subscribe to listen timer's events
        """
        self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)

    def orders(self):
        """
        Return orders

        :return:    list of Order objects
        """
        return self.__orders

    def __on_market_close(self, date, previous_date):
        """
        Market Close event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # print EventType.MARKET_CLOSE, date, previous_date

        # TODO also check if there is market data for this date, same as in trading systems (AND set previous date accordingly? - different than market date)
        # TODO do I need to do all these if there is no position open?

        self.__mark_to_market(date)
        self.__translate_fx_balances(date, previous_date)
        self.__charge_interest(date, previous_date)
        self.__pay_interest(date, previous_date)
        self.__update_margin_loans(date)

        if not self.__portfolio.open_positions():
            self.__sweep_fx_funds(date)

        # print 'FX Balances', self.__account.to_fx_balance_string()

        # TODO Fx hedge
        # TODO cash management (3Mo IR?)

    def transfer(self, order):
        """
        Create Transactions from Orders and transfer them for execution

        :param order:   an Order instance to transfer
        :return:        OrderResult instance
        """
        market = order.market()
        order_date = order.date()
        slippage = Decimal(market.slippage(order_date))
        commissions = self.__commissions(order.quantity(), market.currency(), order_date)
        previous_last_price = market.data(end_date=order_date)[-2][5]
        margin = market.margin(previous_last_price) * Decimal(order.quantity())
        price = (order.price() + slippage) if (order.type() == OrderType.BTO or order.type() == OrderType.BTC) else (order.price() - slippage)  # TODO pass in slippage separe?
        market_position = self.__portfolio.market_position(market)
        # print 'new order: ', order, ', already open positions: ', market_position
        if market_position:
            # -to-close transactions TODO do I need this check? The orders already know this!

            mtm = market_position.mark_to_market(order.date(), price) * Decimal(market_position.quantity()) * market.point_value()
            transaction1 = Transaction(
                TransactionType.MTM_TRANSACTION,
                order.date(),
                mtm,
                market.currency(),
                (market, price)
            )

            self.__account.add_transaction(transaction1)

            # print transaction1, float(self.__account.equity(order_date)), float(self.__account.available_funds(order_date))

            transaction2 = Transaction(
                TransactionType.COMMISSION,
                order.date(),
                -commissions,
                market.currency(),
                (market, order, price)
            )

            self.__account.add_transaction(transaction2)

            # print transaction2, float(self.__account.equity(order_date)), float(self.__account.available_funds(order_date))

            transaction3 = Transaction(
                TransactionType.MARGIN_LOAN,
                order.date(),
                -margin,
                market.currency(),
                'remove'
            )

            self.__account.add_transaction(transaction3)

            # print transaction3, float(self.__account.equity(order_date)), float(self.__account.available_funds(order_date))

            self.__portfolio.remove_position(market_position)

            # print 'Position closed ', self.__account.to_fx_balance_string()
        else:
            # -to-open transactions
            # print 'Enough funds? ', self.__account.available_funds(order_date), self.__account.base_value(margin + commissions, market.currency(), order_date)

            if self.__account.available_funds(order_date) > self.__account.base_value(margin + commissions, market.currency(), order_date):

                transaction1 = Transaction(
                    TransactionType.MARGIN_LOAN,
                    order.date(),
                    margin,
                    market.currency(),
                    'add'
                )

                self.__account.add_transaction(transaction1)

                # print transaction1, float(self.__account.equity(order_date)), float(self.__account.available_funds(order_date))

                transaction2 = Transaction(
                    TransactionType.COMMISSION,
                    order.date(),
                    -commissions,
                    market.currency(),
                    (market, order, price)
                )

                self.__account.add_transaction(transaction2)

                # print transaction2, float(self.__account.equity(order_date)), float(self.__account.available_funds(order_date))

                position = Position(market, {
                        OrderType.BTO: Direction.LONG,
                        OrderType.STO: Direction.SHORT
                    }.get(order.type()),
                    order.date(),
                    order.price(),
                    price,
                    order.quantity(),
                    (order.date(), margin))

                self.__portfolio.add_position(position)

        self.__orders.append(order)

        return OrderResult(OrderResultType.FILLED, order.date(), price, commissions)

    def __commissions(self, quantity, currency, date):
        """
        Calculate and return amount of commission

        :param quantity:    Number of contracts
        :param currency:    Currency denomination of the contract
        :param date:        Date on which to make the commission calculation
        :return:            Commission amount
        """
        commission_value = self.__commission[0]
        if currency == self.__account.base_currency():
            commission_value = commission_value * quantity
        else:
            base_commission = self.__account.base_value(commission_value * quantity, currency, date)
            commission_value = self.__account.fx_value(base_commission, currency, date)
        return commission_value

    def __sweep_fx_funds(self, date):
        """
        Transfer funds from non-base currency to base-currency balance

        :param date:    date of the transfer
        :return:
        """
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            balance = self.__account.fx_balance(currency)

            if abs(balance):
                amount = self.__account.base_value(balance, currency, date)
                fx_transaction = Transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, -balance, currency)
                base_transaction = Transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, amount, base_currency)

                if fx_transaction.account_action() == AccountAction.DEBIT:
                    self.__account.add_transaction(fx_transaction)
                    # print fx_transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))
                    self.__account.add_transaction(base_transaction)
                    # print base_transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))
                else:
                    self.__account.add_transaction(base_transaction)
                    # print base_transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))
                    self.__account.add_transaction(fx_transaction)
                    # print fx_transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))

    def __mark_to_market(self, date):
        """
        Mark open positions to market values

        :param date:    date to which mark the positions
        """
        for p in self.__portfolio.open_positions():
            market = p.market()

            if market.has_data(date):
                price = market.data(end_date=date)[-1][5]
                mtm = p.mark_to_market(date, price) * Decimal(p.quantity()) * p.market().point_value()
                mtm_type = TransactionType.MTM_TRANSACTION if p.date() == date else TransactionType.MTM_POSITION
                transaction = Transaction(mtm_type, date, mtm, market.currency(), (market, price))

                self.__account.add_transaction(transaction)

                # print transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))

    def __translate_fx_balances(self, date, previous_date):
        """
        Translate currency changes in non-base Fx balances

        :param date:            date of the translation
        :param previous_date:   date of previous data
        """
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            pair = [cp for cp in self.__currency_pairs if cp.code() == '%s%s' % (base_currency, currency)][0]
            rate = pair.rate(date)
            prior_rate = pair.rate(previous_date)
            balance = self.__account.fx_balance(currency, previous_date)
            base_value = balance / rate
            prior_base_value = balance / prior_rate
            translation = base_value - prior_base_value

            if abs(translation):
                transaction = Transaction(
                    TransactionType.FX_BALANCE_TRANSLATION,
                    date,
                    translation,
                    base_currency,
                    (balance, currency, rate, prior_rate)
                )

                self.__account.add_transaction(transaction)

                # print transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))

    def __update_margin_loans(self, date):
        """
        Update margin loans with data on the date passed in

        :param date:    date of the data to use for margin calculation
        """
        if len(self.__portfolio.open_positions()):
            margin_loans_to_open = defaultdict(Decimal)
            margin_loans_to_close = defaultdict(Decimal)

            for p in self.__portfolio.open_positions():
                if date > p.date():
                    market = p.market()

                    if market.has_data(date):
                        margin = market.margin(market.data(end_date=date)[-1][5]) * Decimal(p.quantity())
                        currency = market.currency()
                        margin_loans_to_close[currency] += Decimal(p.margins()[-1][1])
                        margin_loans_to_open[currency] += Decimal(margin)
                        p.add_margin(date, margin)

            for currency in margin_loans_to_close.keys():
                debit_transaction = Transaction(
                    TransactionType.MARGIN_LOAN,
                    date,
                    -margin_loans_to_close[currency],
                    currency,
                    'update'
                )
                self.__account.add_transaction(debit_transaction)

                # print debit_transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))

            for currency in margin_loans_to_open.keys():
                credit_transaction = Transaction(
                    TransactionType.MARGIN_LOAN,
                    date,
                    margin_loans_to_open[currency],
                    currency,
                    'update'
                )
                self.__account.add_transaction(credit_transaction)

                # print credit_transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))

    def __charge_interest(self, date, previous_date):
        """
        Charge interest on the account's margin loan balances

        :param date:            date of the charge
        :param previous_date:   date of interest calculation (previous date for overnight margins)
        """
        days = 365
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.margin_loan_currencies() if c != base_currency]:
            spread = Decimal(2.0)
            balance = self.__account.margin_loan_balance(currency, previous_date)

            if balance:
                benchmark_interest = [r for r in self.__interest_rates if r.code() == currency][0]
                rate = (benchmark_interest.immediate_rate(previous_date) + spread) / 100
                amount = balance * rate / days

                transaction = Transaction(
                    TransactionType.INTEREST,
                    date,
                    -amount,
                    currency,
                    (balance, benchmark_interest, rate, 'margin')
                )
                self.__account.add_transaction(transaction)

                # print transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))

        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            spread = Decimal(2.0)
            balance = self.__account.fx_balance(currency, previous_date)

            if balance < 0:
                benchmark_interest = [r for r in self.__interest_rates if r.code() == currency][0]
                rate = (benchmark_interest.immediate_rate(previous_date) + spread) / 100
                amount = balance * rate / days

                transaction = Transaction(
                    TransactionType.INTEREST,
                    date,
                    amount,
                    currency,
                    (balance, benchmark_interest, rate, 'balance')
                )
                self.__account.add_transaction(transaction)

                # print transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))

    def __pay_interest(self, date, previous_date):
        """
        Pay interest to the account's cash balances

        :param date:            Date of the charge
        :param previous_date:   Date of interest calculation (previous date for overnight margins)
        """
        days = 365
        for currency in [c for c in self.__account.fx_balance_currencies()]:
            spread = Decimal(0.5)
            # TODO pass in in config
            minimums = {'AUD': 14000, 'CAD': 14000, 'CHF': 100000, 'EUR': 100000, 'GBP': 8000, 'JPY': 11000000, 'USD': 10000}
            balance = self.__account.fx_balance(currency, previous_date)

            if balance - minimums[currency] > 0:
                benchmark_interest = [r for r in self.__interest_rates if r.code() == currency][0]
                rate = (benchmark_interest.immediate_rate(previous_date) - spread) / 100
                amount = (balance - minimums[currency]) * rate / days

                transaction = Transaction(
                    TransactionType.INTEREST,
                    date,
                    amount,
                    currency,
                    (balance - minimums[currency], benchmark_interest, rate, 'balance')
                )
                self.__account.add_transaction(transaction)

                # print transaction, float(self.__account.equity(date)), float(self.__account.available_funds(date))
