#!/usr/bin/python

from enum import OrderType
from enum import OrderResultType
from enum import TransactionType
from enum import EventType
from enum import Table
from transaction import Transaction
from order_result import OrderResult
from collections import defaultdict
from decimal import Decimal
import operator as op


class Broker(object):

    def __init__(self, timer, account, portfolio, commission, currency_pairs, interest_rates, minimums):
        self.__timer = timer
        self.__account = account
        self.__portfolio = portfolio
        self.__commission = commission
        self.__currency_pairs = currency_pairs
        self.__interest_rates = interest_rates
        self.__minimums = minimums
        self.__order_results = []

    def subscribe(self):
        """
        Subscribe to listen timer's events
        """
        self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)

    def order_results(self):
        """
        Return OrderResults

        :return:    list of OrderResult objects
        """
        return self.__order_results

    def __on_market_close(self, date, previous_date):
        """
        Market Close event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # TODO also check if there is market data for this date, same as in trading systems (AND set previous date accordingly? - different than market date)
        # TODO do I need to do all these if there is no position open?

        self.__mark_to_market(date)
        self.__translate_fx_balances(date, previous_date)
        self.__charge_interest(date, previous_date)
        self.__pay_interest(date, previous_date)
        self.__update_margin_loans(date)

        if not self.__portfolio.open_positions():
            self.__sweep_fx_funds(date)

        # TODO Fx hedge
        # TODO cash management (3Mo IR?)

    def transfer(self, order):
        """
        Create Transactions from Orders and transfer them for execution

        :param order:   an Order instance to transfer
        :return:        OrderResult instance
        """
        market = order.market()
        date = order.date()
        order_type = order.type()
        currency = market.currency()
        slippage = Decimal(market.slippage(date))
        commissions = self.__commissions(order.quantity(), market.currency(), date)
        previous_last_price = market.data(end_date=date)[-2][Table.Market.SETTLE_PRICE]
        margin = market.margin(previous_last_price) * Decimal(order.quantity())
        price = (order.price() + slippage) if (order.type() == OrderType.BTO or order.type() == OrderType.BTC) else (order.price() - slippage)  # TODO pass in slippage separe?
        order_result = OrderResult(OrderResultType.REJECTED, order, price, margin, commissions)

        if order_type == OrderType.BTO or order_type == OrderType.STO:
            if self.__account.available_funds(date) > self.__account.base_value(margin + commissions, currency, date):
                self.__add_transaction(TransactionType.MARGIN_LOAN, date, margin, currency, 'add')
                self.__add_transaction(TransactionType.COMMISSION, date, -commissions, currency, (market, order, price))

                order_result = OrderResult(OrderResultType.FILLED, order, price, margin, commissions)
        else:
            position = self.__portfolio.market_position(market)
            mtm = position.mark_to_market(order.date(), price) * Decimal(position.quantity()) * market.point_value()

            self.__add_transaction(TransactionType.MTM_TRANSACTION, date, mtm, currency, (market, price))
            self.__add_transaction(TransactionType.COMMISSION, date, -commissions, currency, (market, order, price))
            self.__add_transaction(TransactionType.MARGIN_LOAN, date, -margin, currency, 'remove')

            order_result = OrderResult(OrderResultType.FILLED, order, price, margin, commissions)

        self.__order_results.append(order_result)
        return order_result

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
                if balance > 0:
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, -balance, currency)
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, amount, base_currency)
                else:
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, amount, base_currency)
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, -balance, currency)

    def __mark_to_market(self, date):
        """
        Mark open positions to market values

        :param date:    date to which mark the positions
        """
        for p in self.__portfolio.open_positions():
            market = p.market()

            if market.has_data(date):
                price = market.data(end_date=date)[-1][Table.Market.SETTLE_PRICE]
                mtm = p.mark_to_market(date, price) * Decimal(p.quantity()) * market.point_value()
                mtm_type = TransactionType.MTM_TRANSACTION if p.latest_enter_date() == date else TransactionType.MTM_POSITION
                self.__add_transaction(mtm_type, date, mtm, market.currency(), (market, price))

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

            if rate != prior_rate:
                balance = self.__account.fx_balance(currency, previous_date)
                base_value = balance / rate
                prior_base_value = balance / prior_rate
                translation = base_value - prior_base_value
                context = (balance, currency, rate, prior_rate)
                self.__add_transaction(TransactionType.FX_BALANCE_TRANSLATION, date, translation, base_currency, context)

    def __update_margin_loans(self, date):
        """
        Update margin loans with data on the date passed in

        :param date:    date of the data to use for margin calculation
        """
        if len(self.__portfolio.open_positions()):
            to_open = defaultdict(Decimal)
            to_close = defaultdict(Decimal)

            for p in self.__portfolio.open_positions():
                if date > p.enter_date():
                    market = p.market()

                    if market.has_data(date):
                        margin = market.margin(market.data(end_date=date)[-1][Table.Market.SETTLE_PRICE]) * Decimal(p.quantity())
                        currency = market.currency()
                        to_close[currency] += Decimal(p.margins()[-1][1])
                        to_open[currency] += Decimal(margin)
                        p.add_margin(date, margin)

            for k in to_close.keys():
                self.__add_transaction(TransactionType.MARGIN_LOAN, date, -to_close[k], k, 'update')

            for k in to_open.keys():
                self.__add_transaction(TransactionType.MARGIN_LOAN, date, to_open[k], k, 'update')

    def __charge_interest(self, date, previous_date):
        """
        Charge interest on the account's margin loan balances

        :param date:            date of the charge
        :param previous_date:   date of interest calculation (previous date for overnight margins)
        """
        minimums = {m: 0 for m in self.__minimums.keys()}
        spread = Decimal(2.0)

        map(lambda c: self.__interest(c, minimums[c], spread, op.ne, op.add, -1, date, previous_date, 'margin'),
            [c for c in self.__account.margin_loan_currencies() if c != self.__account.base_currency()])

        map(lambda c: self.__interest(c, minimums[c], spread, op.lt, op.add, 1, date, previous_date, 'balance'),
            [c for c in self.__account.fx_balance_currencies() if c != self.__account.base_currency()])

    def __pay_interest(self, date, previous_date):
        """
        Pay interest to the account's cash balances

        :param date:            Date of the charge
        :param previous_date:   Date of interest calculation (previous date for overnight margins)
        """
        spread = Decimal(0.5)

        map(lambda c: self.__interest(c, self.__minimums[c], spread, op.gt, op.sub, 1, date, previous_date, 'balance'),
            self.__account.fx_balance_currencies())

    def __interest(self, currency, minimum, spread, condition, spread_op, sign, date, previous_date, target):
        """
        Calculates interest amount and add respective transaction

        :param currency:        currency symbol of the balance
        :param minimum:         balance cut-off minimums
        :param spread:          spread to combine rate with
        :param condition:       condition to check in order to add transaction
        :param spread_op:       either add or subtract spread to the rate
        :param sign:            sign of the interest amount
        :param date:            date of the transaction
        :param previous_date:   previous date
        :param target:          target balance, either margin-loan or fx-balance
        """
        days = 365
        transaction_type = TransactionType.BALANCE_INTEREST if target == 'balance' else TransactionType.MARGIN_INTEREST
        fn = self.__account.fx_balance if target == 'balance' else self.__account.margin_loan_balance
        balance = fn(currency, previous_date) - minimum

        if condition(balance, 0):
            benchmark_interest = [r for r in self.__interest_rates if r.code() == currency][0]
            rate = spread_op(benchmark_interest.immediate_rate(previous_date), spread) / 100
            amount = balance * rate / days
            context = (balance, benchmark_interest, rate, target)
            self.__add_transaction(transaction_type, date, amount * sign, currency, context)

    def __add_transaction(self, transaction_type, date, amount, currency, context_data=None):
        """
        Helper function that creates and adds an transaction to the account

        :param transaction_type:    string, type of transaction
        :param date:                date of the transaction
        :param amount:              amount of the transaction
        :param currency:            string - currency symbol of the transaction amount
        :param context_data:        tuple - variable context data
        """
        self.__account.add_transaction(Transaction(transaction_type, date, amount, currency, context_data))
