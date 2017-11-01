#!/usr/bin/python

from math import floor
from enum import OrderType
from enum import OrderResultType
from enum import TransactionType
from enum import Table
from enum import Study
from trade import Trade
from order_result import OrderResult
from transaction import Transaction
from collections import defaultdict
from decimal import Decimal
import operator as op
import datetime as dt


class Broker(object):

    def __init__(self, account, commission, interest_rates, minimums, markets):
        self.__account = account
        self.__commission = commission[0]
        self.__commission_currency = commission[1]
        self.__interest_rates = interest_rates
        self.__minimums = minimums
        self.__markets = markets
        self.__trade_records = []
        self.__trade_indexes = defaultdict(list)
        self.__position_records = {}

    def update_account(self, date, previous_date):
        """
        Market Close event handler

        :param date:                date for the market open
        :param previous_date:       previous market date
        """
        self.__record_positions(date, previous_date)

        self.__mark_to_market(date, previous_date)
        self.__translate_fx_balances(date, previous_date)
        self.__charge_interest(date, previous_date)
        self.__pay_interest(date, previous_date)

        # TODO Sweep regularly?
        if not self.positions(date):
            self.__sweep_fx_funds(date)

        # TODO Fx hedge
        # TODO cash management (3Mo IR bonds?)

    def transfer(self, order, target_position_size, open_position):
        """
        Create Transactions from Orders and transfer them for execution

        :param order:           an Order instance to transfer
        :param open_positions:  list of open positions
        :return:                OrderResult instance
        """
        market = order.market()
        volume = market.study(Study.VOL_SHORT)[Table.Study.VALUE]
        quantity = order.quantity() if order.quantity() <= volume else floor(volume / 3)
        order_result = OrderResult(OrderResultType.REJECTED, order, order.price(), quantity, 0, 0)

        if quantity:
            date = order.date()
            added = abs(open_position) < abs(target_position_size)
            market_data, previous_data = market.data(date)
            previous_date = previous_data[Table.Market.PRICE_DATE]
            commissions = Decimal(self.__commission * abs(quantity))
            margin = market.margin() * abs(quantity) * (1 if added else -1)
            price = self.__slipped_price(market_data, market, order.price(), previous_date, quantity)
            result_type = OrderResultType.FILLED if quantity == order.quantity() else OrderResultType.PARTIALLY_FILLED
            order_result = OrderResult(result_type, order, price, quantity, margin, commissions)
            context = (market, order_result, price)
            margin_loan_context = 'add' if added else 'remove'

            self.__add_transaction(TransactionType.MARGIN_LOAN, date, margin, market.currency(), margin_loan_context)
            self.__add_transaction(TransactionType.COMMISSION, date, -commissions, self.__commission_currency, context)

            self.__trade_records.append(Trade(order, order_result))
            self.__trade_indexes[date].append(len(self.__trade_records) - 1)

        return order_result

    def trades(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31), strict=False):
        """
        Find and return positions within the dates specified (included)

        :param start_date:  Start date to search from
        :param end_date:    End date to search until
        :param strict:      Boolean flag indicating 'strict' mode -- if dates are not in dict, return empty list
        :return:            list of Trade objects
        """
        # TODO its own data-type? Identical to Account's 'transactions'
        contains_start = start_date in self.__trade_indexes
        contains_end = end_date in self.__trade_indexes
        start_indexes = self.__trade_indexes[start_date] if contains_start \
            else self.__trade_indexes[sorted(self.__trade_indexes)[0]] if len(self.__trade_indexes) \
            else []

        end_indexes = start_indexes if start_date == end_date \
            else self.__trade_indexes[end_date] if contains_end \
            else self.__trade_indexes[sorted(self.__trade_indexes)[-1]] if len(self.__trade_indexes) \
            else []

        start_index = sorted(start_indexes)[0] if len(start_indexes) else 0
        end_index = sorted(end_indexes)[-1] if len(end_indexes) else len(self.__trade_records) - 1

        return self.__trade_records[start_index:end_index+1] if not strict else \
            self.__trade_records[start_index:end_index+1] if contains_start and contains_end else []

    def __record_positions(self, date, previous_date):
        """
        Record position for the date passed in from executed trades, if any
        
        :param date:            date of the record
        :param previous_date:   previous date
        """
        previous_record = self.__position_records[previous_date] if previous_date in self.__position_records else {}
        open_positions = previous_record.copy()
        for t in self.trades(date, date, True):
            order = t.order()
            key = '%s_%s' % (order.market().id(), order.contract())
            quantity = t.result().quantity()
            open_positions[key] = previous_record[key] + quantity if key in previous_record else quantity

        self.__position_records[date] = {k: open_positions[k] for k in open_positions.keys() if open_positions[k]}

    def positions(self, date):
        """
        Return positions for the date passed in, if any
        
        :param datetime date:   date of the positions
        :return dict:           {<'market ID'_'contract'>: <number of positions>}
        """
        return self.__position_records[date] if date in self.__position_records else {}

    def __slipped_price(self, market_data, market, price, date, quantity):
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
        slippage = market.slippage(date, abs(quantity))
        slipped_price = (price + slippage) if quantity > 0 else (price - slippage)
        # TODO add 'execution cost (market impact)' transaction instead of slipped price?
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
                self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, amount, base_currency)
                self.__add_transaction(TransactionType.INTERNAL_FUND_TRANSFER, date, -balance, currency)

    def __mark_to_market(self, date, previous_date):
        """
        Mark open positions to market values

        :param date:            date to which mark the positions
        :param previous_date:   previous trading date
        """
        open_positions = self.positions(previous_date)
        order_results = {'%s_%s' % (t.order().market().id(), t.order().contract()): t.result()
                         for t in self.trades(date, date, True)}
        not_traded_positions = {k: open_positions[k] + (order_results[k].quantity() if k in order_results else 0)
                                for k in open_positions.keys()}
        # MTM transactions
        for k in order_results.keys():
            market = self.__markets[int(k.split('_')[0])]
            market_data, previous_data = market.data(date)
            contract = k.split('_')[1]
            order_result = order_results[k]
            price = order_result.price()
            quantity = order_result.quantity()
            settle_price = market_data[Table.Market.SETTLE_PRICE]
            previous_settle_price = previous_data[Table.Market.SETTLE_PRICE]
            order_type = {
                1: {1: {1: OrderType.BTO, 0: OrderType.STC}, 0: {1: OrderType.BTC, 0: OrderType.STO}},
                0: {0: {1: OrderType.BTO, 0: OrderType.STO}}
            }[int(k in open_positions)][int(k in open_positions and open_positions[k] > 0)][int(quantity > 0)]
            pnl = {
                OrderType.BTO: settle_price - price,
                OrderType.STO: price - settle_price,
                OrderType.BTC: previous_settle_price - price,
                OrderType.STC: price - previous_settle_price
            }[order_type]
            context = {
                OrderType.BTO: (market, contract, settle_price),
                OrderType.STO: (market, contract, settle_price),
                OrderType.BTC: (market, contract, price),
                OrderType.STC: (market, contract, price)
            }[order_type]
            pnl = Decimal(pnl * abs(quantity) * market.point_value())
            self.__add_transaction(TransactionType.MTM_TRANSACTION, date, pnl, market.currency(), context)

        # MTM Positions
        for k in not_traded_positions.keys():
            market = self.__markets[int(k.split('_')[0])]
            market_data, previous_data = market.data(date)
            quantity = not_traded_positions[k]
            if market_data and quantity:
                price = market_data[Table.Market.SETTLE_PRICE]
                previous_settle_price = previous_data[Table.Market.SETTLE_PRICE]
                pnl = price - previous_settle_price if quantity > 0 else previous_settle_price - price
                context = (market, k.split('_')[1], price)
                pnl = Decimal(pnl * abs(quantity) * market.point_value())
                self.__add_transaction(TransactionType.MTM_POSITION, date, pnl, market.currency(), context)

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
