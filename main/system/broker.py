#!/usr/bin/python

from math import floor
from enum import Direction
from enum import OrderType
from enum import SignalType
from enum import OrderResultType
from enum import TransactionType
from enum import Table
from enum import Study
from transaction import Transaction
from order_result import OrderResult
from collections import defaultdict
from decimal import Decimal
import operator as op


class Broker(object):

    def __init__(self, account, commission, interest_rates, minimums):
        self.__account = account
        self.__commission = commission[0]
        self.__commission_currency = commission[1]
        self.__interest_rates = interest_rates
        self.__minimums = minimums

    def update_account(self, date, previous_date, open_positions, removed_positions):
        """
        Market Close event handler

        :param date:                date for the market open
        :param previous_date:       previous market date
        :param open_positions:      list of open positions
        :param removed_positions:   list of positions removed from portfolio on this date
        """
        # TODO also check if there is market data for this date, same as in trading systems (AND set previous date accordingly? - different than market date)
        # TODO do I need to do all these if there is no position open?

        self.__mark_to_market(date, open_positions, removed_positions)
        self.__translate_fx_balances(date, previous_date)
        self.__charge_interest(date, previous_date)
        self.__pay_interest(date, previous_date)
        # No need to update margin loans since I use fixed amounts
        # self.__update_margin_loans(date, open_positions)

        # TODO Sweep regularly?
        if not open_positions:
            self.__sweep_fx_funds(date)

        # TODO Fx hedge
        # TODO cash management (3Mo IR?)

    def transfer(self, order, open_positions):
        """
        Create Transactions from Orders and transfer them for execution

        :param order:           an Order instance to transfer
        :param open_positions:  list of open positions
        :return:                OrderResult instance
        """
        market = order.market()
        date = order.date()
        order_type = order.type()
        currency = market.currency()
        market_data, previous_data = market.data(date)
        previous_date = previous_data[Table.Market.PRICE_DATE]
        volume = market.study(Study.VOL_SHORT)[Table.Study.VALUE]
        quantity = order.quantity() if order.quantity() <= volume else floor(volume / 3)
        order_result = OrderResult(OrderResultType.REJECTED, order, order.price(), quantity, 0, 0)
        # TODO what about rejected EXIT orders?! (Taken care of by position-sizing rebalance?)
        if quantity:
            commissions = Decimal(self.__commission * quantity)
            margin = market.margin() * quantity
            price = self.__slipped_price(market_data, market, order.price(), previous_date, order_type, quantity)
            result_type = OrderResultType.FILLED if quantity == order.quantity() else OrderResultType.PARTIALLY_FILLED
            order_result = OrderResult(result_type, order, price, quantity, margin, commissions)
            context = (market, order_result, price)

            # TODO don't need types -- just quantity and Qty == 0 means no position
            if order_type == OrderType.BTO or order_type == OrderType.STO:
                base_commission = self.__account.base_value(commissions, self.__commission_currency, date)
                base_margin = Decimal(self.__account.base_value(margin, currency, date))
                if self.__account.available_funds(date) > base_margin + base_commission:
                    margin_loan_context = 'update' if order.signal_type() == SignalType.REBALANCE else 'add'
                    self.__add_transaction(TransactionType.MARGIN_LOAN, date, margin, currency, margin_loan_context)
                    self.__add_transaction(TransactionType.COMMISSION, date, -commissions, self.__commission_currency, context)
            else:
                margin_loan_context = 'update' if order.signal_type() == SignalType.REBALANCE else 'remove'
                self.__add_transaction(TransactionType.COMMISSION, date, -commissions, self.__commission_currency, context)
                self.__add_transaction(TransactionType.MARGIN_LOAN, date, -margin, currency, margin_loan_context)

        return order_result

    def __slipped_price(self, market_data, market, price, date, order_type, quantity):
        """
        Calculate and return price after slippage is added

        :param market_data: tuple of the market day data
        :param market       market to calculate the slippage for
        :param price        order price
        :param date         date for the slippage calculation
        :param order_type:  type of order
        :param quantity:    quantity to open
        :return:            number representing final price
        """
        slippage = market.slippage(date, quantity)
        slipped_price = (price + slippage) if (order_type == OrderType.BTO or order_type == OrderType.BTC) else (price - slippage)
        # TODO add 'execution cost' transaction instead of slipped price? And update only Open price on Market Open?
        # The High and Low prices are not actually available at this point (Market Open),
        # but I'm using them here to not getting execution price out of price range
        high = market_data[Table.Market.HIGH_PRICE]
        low = market_data[Table.Market.LOW_PRICE]
        return high if slipped_price > high else (low if slipped_price < low else slipped_price)

    def __sweep_fx_funds(self, date):
        """
        Transfer funds from non-base currency to base-currency balance

        :param date:    date of the transfer
        :return:
        """
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            balance = self.__account.fx_balance(currency, date)

            if abs(balance):
                amount = self.__account.base_value(balance, currency, date)
                if balance > 0:
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, -balance, currency)
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, amount, base_currency)
                else:
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, amount, base_currency)
                    self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, -balance, currency)

    def __mark_to_market(self, date, open_positions, removed_positions):
        """
        Mark open positions to market values

        :param date:                date to which mark the positions
        :param open_positions:      list of open positions
        :param removed_positions:   list of positions removed from portfolio on this date
        """
        transactions = [t for t in self.__account.transactions(date, date) if t.type() == TransactionType.COMMISSION]
        transactions_pnl = {}
        for t in transactions:
            market = t.context()[0]
            order_result = t.context()[1]
            order = order_result.order()
            order_type = order.type()
            market_data, previous_data = market.data(date)
            price = order_result.price()
            settle_price = market_data[Table.Market.SETTLE_PRICE]
            previous_settle_price = previous_data[Table.Market.SETTLE_PRICE]
            positions = removed_positions if order.signal_type() == SignalType.EXIT else open_positions
            position = [p for p in positions if p.market() == market][0]
            pnl = {
                OrderType.BTO: settle_price - price,
                OrderType.STO: price - settle_price,
                OrderType.BTC: previous_settle_price - price,
                OrderType.STC: price - previous_settle_price
            }[order_type]
            context = {
                OrderType.BTO: (market, order.contract(), settle_price),
                OrderType.STO: (market, order.contract(), settle_price),
                OrderType.BTC: (market, order.contract(), price),
                OrderType.STC: (market, order.contract(), price)
            }[order_type]
            position.update_pnl(date, settle_price, pnl, order_result.quantity())
            pnl = Decimal(pnl * order_result.quantity() * market.point_value())
            transactions_pnl[market.id()] = pnl

            self.__add_transaction(TransactionType.MTM_TRANSACTION, date, pnl, market.currency(), context)
            print 'Transaction', market.id(), market.code(), order_type, order_result.type(), order_result.quantity(), \
                price, round(pnl, 3)

        for p in open_positions:
            market = p.market()
            market_data, previous_data = market.data(date)
            position_quantity = p.position_quantity(date)

            if market_data and position_quantity:
                price = market_data[Table.Market.SETTLE_PRICE]
                previous_price = previous_data[Table.Market.SETTLE_PRICE]
                pnl = price - previous_price if p.direction() == Direction.LONG else previous_price - price

                print 'Position', market.id(), market.code(), position_quantity, p.quantity(), \
                    price, round(pnl * position_quantity * market.point_value(), 3)
                p.update_pnl(date, price, pnl, position_quantity)
                pnl = Decimal(pnl * position_quantity * market.point_value())
                self.__add_transaction(TransactionType.MTM_POSITION, date, pnl, market.currency(), (market, p.contract(), price))

    def __translate_fx_balances(self, date, previous_date):
        """
        Translate currency changes in non-base Fx balances

        :param date:            date of the translation
        :param previous_date:   date of previous data
        """
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            rate = Decimal(self.__account.base_rate(currency, date))
            prior_rate = Decimal(self.__account.base_rate(currency, previous_date))
            balance = self.__account.fx_balance(currency, previous_date)

            if rate != prior_rate and balance:
                base_value = balance / rate
                prior_base_value = balance / prior_rate
                translation = base_value - prior_base_value
                context = (balance, currency, rate, prior_rate)
                self.__add_transaction(TransactionType.FX_BALANCE_TRANSLATION, date, translation, base_currency, context)

    def __update_margin_loans(self, date, open_positions):
        """
        Update margin loans with data on the date passed in

        :param date:            date of the data to use for margin calculation
        :param open_positions:  list of open positions
        """
        if len(open_positions):
            to_open = defaultdict(float)
            to_close = defaultdict(float)

            for p in open_positions:
                if date > p.enter_date():
                    market = p.market()
                    market_data, _ = market.data(date)

                    if market_data:
                        margin = market.margin() * p.quantity()
                        currency = market.currency()
                        to_close[currency] += p.margins()[-1][1]
                        to_open[currency] += margin
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
        spread = 2.0

        map(lambda c: self.__interest(c, minimums.get(c, 0), spread, op.ne, op.add, -1, date, previous_date, 'margin'),
            [c for c in self.__account.margin_loan_currencies() if c != self.__account.base_currency()])

        map(lambda c: self.__interest(c, minimums.get(c, 0), spread, op.lt, op.add, 1, date, previous_date, 'balance'),
            [c for c in self.__account.fx_balance_currencies() if c != self.__account.base_currency()])

    def __pay_interest(self, date, previous_date):
        """
        Pay interest to the account's cash balances

        :param date:            Date of the charge
        :param previous_date:   Date of interest calculation (previous date for overnight margins)
        """
        spread = 0.5

        map(lambda c: self.__interest(c, self.__minimums.get(c, 0), spread, op.gt, op.sub, 1, date, previous_date, 'balance'),
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
        balance = Decimal(fn(currency, previous_date) - minimum)

        if condition(balance, 0):
            currency_rates = [r for r in self.__interest_rates if r.code() == currency]
            benchmark_interest = currency_rates[0] if len(currency_rates) else None
            immediate_rate = benchmark_interest.immediate_rate(previous_date) if benchmark_interest else 0
            rate = Decimal(spread_op(immediate_rate, spread) / 100)
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
