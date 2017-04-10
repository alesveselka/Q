#!/usr/bin/python

from enum import Direction
from enum import OrderType
from enum import OrderResultType
from enum import TransactionType
from enum import AccountAction
from enum import EventType
from enum import Study
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

    def __on_market_close(self, date, previous_date):
        """
        Market Close event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        print EventType.MARKET_CLOSE, date, previous_date

        # TODO also check if there is market data for this date, same as in trading systems (AND set previous date accordingly? - different than market date)
        # TODO do I need to do all these if there is no position open?

        self.__mark_to_market(date)
        self.__translate_fx_balances(date, previous_date)
        self.__charge_interest(date, previous_date)
        self.__pay_interest(date, previous_date)
        self.__update_margin_loans(date)

        if not self.__portfolio.positions():
            self.__sweep_fx_funds(date)

        print 'FX Balances', self.__account.to_fx_balance_string()

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
        market_data = market.data(end_date=order_date)
        atr_short = market.study(Study.ATR_SHORT, order_date)[-1][1]
        volume_short = market.study(Study.VOL_SHORT, order_date)[-1][1]
        slippage = Decimal(market.slippage(volume_short, atr_short))
        commission = self.__commission * order.quantity()
        previous_last_price = market_data[-2][5]
        margin = market.margin(previous_last_price) * order.quantity()
        price = (order.price() + slippage) if (order.type() == OrderType.BTO or order.type() == OrderType.BTC) else (order.price() - slippage)  # TODO pass in slippage separe?
        positions_in_market = self.__portfolio.positions_in_market(market)
        print 'new order: ', order, ', already open positions: ', positions_in_market
        if len(positions_in_market):
            # -to-close transactions TODO do I need this check? The orders already know this!

            position = positions_in_market[0]  # TODO what if there is more than one position?
            mtm = position.mark_to_market(order.date(), price) * Decimal(position.quantity()) * market.point_value()
            transaction1 = Transaction(
                TransactionType.MTM_TRANSACTION,
                AccountAction.CREDIT if mtm > 0 else AccountAction.DEBIT,
                order.date(),
                abs(mtm),
                market.currency(),
                price
                # 'MTM %.2f(%s) at %.2f' % (float(mtm), market.currency(), price)
            )

            self.__account.add_transaction(transaction1)

            print transaction1, float(self.__account.equity()), float(self.__account.available_funds())

            transaction2 = Transaction(
                TransactionType.COMMISSION,
                AccountAction.DEBIT,
                order.date(),
                commission,
                market.currency(),  # TODO market's currency is not necessarily commission's currency
                (market, order, price)
                # '%s %d x %s at %.2f' % (order.type(), order.quantity(), market.code(), price)
            )

            self.__account.add_transaction(transaction2)

            print transaction2, float(self.__account.equity()), float(self.__account.available_funds())

            transaction3 = Transaction(
                TransactionType.MARGIN_LOAN,
                AccountAction.DEBIT,
                order.date(),
                margin,
                market.currency()
                # 'Close %.2f(%s) margin loan (REMOVE)' % (margin, market.currency())
            )

            self.__account.add_transaction(transaction3)

            print transaction3, float(self.__account.equity()), float(self.__account.available_funds())

            self.__portfolio.remove_position(position)

            print 'Position closed ', self.__account.to_fx_balance_string()
        else:
            # -to-open transactions
            print 'Enough funds? ', self.__account.available_funds(), self.__account.base_value(margin + commission, market.currency())
            if self.__account.available_funds() > self.__account.base_value(margin + commission, market.currency()):

                transaction1 = Transaction(
                    TransactionType.MARGIN_LOAN,
                    AccountAction.CREDIT,
                    order.date(),
                    margin,
                    market.currency()
                    # 'Take %.2f(%s) margin loan (ADD)' % (margin, market.currency())
                )

                self.__account.add_transaction(transaction1)

                print transaction1, float(self.__account.equity()), float(self.__account.available_funds())

                transaction2 = Transaction(
                    TransactionType.COMMISSION,
                    AccountAction.DEBIT,
                    order.date(),
                    commission,
                    market.currency(),  # TODO market's currency is not necessarily commission's currency
                    (market, order, price)
                    # '%s %d x %s at %.2f' % (order.type(), order.quantity(), market.code(), price)
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
                    order.quantity(),
                    (order.date(), margin))

                self.__portfolio.add_position(position)

        return OrderResult(OrderResultType.FILLED, order.date(), price, commission)

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
                amount = self.__account.base_value(balance, currency)
                action = AccountAction.DEBIT if balance > 0 else AccountAction.CREDIT

                fx_transaction = Transaction(
                    TransactionType.INTERNAL_FUND_TRANSFER,
                    action,
                    date,
                    abs(balance),
                    currency
                    # 'Transfer funds, %s of %.4f %s from %s balance' % (action, float(abs(balance)), currency, currency)
                )

                action = AccountAction.CREDIT if action == AccountAction.DEBIT else AccountAction.DEBIT
                base_transaction = Transaction(
                    TransactionType.INTERNAL_FUND_TRANSFER,
                    action,
                    date,
                    abs(amount),
                    base_currency
                    # 'Transfer funds, %s of %.4f %s to %s balance' % (action, float(abs(amount)), base_currency, base_currency)
                )

                if fx_transaction.account_action() == AccountAction.DEBIT:
                    self.__account.add_transaction(fx_transaction)
                    print fx_transaction, float(self.__account.equity()), float(self.__account.available_funds())
                    self.__account.add_transaction(base_transaction)
                    print base_transaction, float(self.__account.equity()), float(self.__account.available_funds())
                else:
                    self.__account.add_transaction(base_transaction)
                    print base_transaction, float(self.__account.equity()), float(self.__account.available_funds())
                    self.__account.add_transaction(fx_transaction)
                    print fx_transaction, float(self.__account.equity()), float(self.__account.available_funds())

    def __mark_to_market(self, date):
        for p in self.__portfolio.positions():
            market = p.market()

            if market.has_data(date):
                price = market.data(end_date=date)[-1][5]
                mtm = p.mark_to_market(date, price) * Decimal(p.quantity()) * p.market().point_value()
                transaction = Transaction(
                    TransactionType.MTM_TRANSACTION if p.date() == date else TransactionType.MTM_POSITION,
                    AccountAction.CREDIT if mtm > 0 else AccountAction.DEBIT,
                    date,
                    abs(mtm),
                    market.currency(),
                    price
                    # 'MTM %.2f(%s) at %.4f' % (float(mtm), market.currency(), price)
                )

                self.__account.add_transaction(transaction)

                print transaction, float(self.__account.equity()), float(self.__account.available_funds())

    def __translate_fx_balances(self, date, previous_date):
        """
        Translate currency changes in non-base Fx balances

        :param date:            date of the translation
        :param previous_date:   date of previous data
        """
        base_currency = self.__account.base_currency()
        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            code = '%s%s' % (base_currency, currency)
            pair = [cp for cp in self.__currency_pairs if cp.code() == code]
            pair_data = pair[0].data(end_date=date)
            # TODO remove hard-coded values
            rate = pair_data[-1][4] if len(pair_data) else Decimal(1)
            # prior_rate = pair_data[-2][4] if len(pair_data) > 1 else rate
            prior_rate = Decimal(1.1)
            balance = self.__account.fx_balance(currency, previous_date)
            base_value = balance / rate
            prior_base_value = balance / prior_rate
            translation = base_value - prior_base_value

            if abs(translation):
                transaction = Transaction(
                    TransactionType.FX_BALANCE_TRANSLATION,
                    AccountAction.CREDIT if translation > 0 else AccountAction.DEBIT,  # TODO auto-determine based on sign?
                    date,
                    abs(translation),
                    base_currency,
                    (balance, currency, rate, prior_rate)
                    # 'FX Translation %.2f(%s) of %.2f(%s), prior: %.4f, current: %.4f' % (float(translation), base_currency, balance, currency, prior_rate, rate)
                )

                self.__account.add_transaction(transaction)

                print transaction, float(self.__account.equity()), float(self.__account.available_funds())

    def __update_margin_loans(self, date):
        """
        Update margin loans with data on the date passed in

        :param date:    date of the data to use for margin calculation
        """
        if len(self.__portfolio.positions()):
            margin_loans_to_open = defaultdict(Decimal)
            margin_loans_to_close = defaultdict(Decimal)

            for p in self.__portfolio.positions():
                if date > p.date():
                    market = p.market()

                    if market.has_data(date):
                        margin = market.margin(market.data(end_date=date)[-1][5]) * p.quantity()
                        currency = market.currency()
                        margin_loans_to_close[currency] += Decimal(p.margins()[-1][1])
                        margin_loans_to_open[currency] += Decimal(margin)
                        p.add_margin(date, margin)

            for currency in margin_loans_to_close.keys():
                debit_transaction = Transaction(
                    TransactionType.MARGIN_LOAN,
                    AccountAction.DEBIT,
                    date,
                    margin_loans_to_close[currency],
                    currency
                    # 'Close %.2f(%s) margin loan (UPDATE)' % (float(margin_loans_to_close[currency]), currency)
                )
                self.__account.add_transaction(debit_transaction)

                print debit_transaction, float(self.__account.equity()), float(self.__account.available_funds())

            for currency in margin_loans_to_open.keys():
                credit_transaction = Transaction(
                    TransactionType.MARGIN_LOAN,
                    AccountAction.CREDIT,
                    date,
                    margin_loans_to_open[currency],
                    currency
                    # 'Take %.2f(%s) margin loan (UPDATE)' % (float(margin_loans_to_open[currency]), currency)
                )
                self.__account.add_transaction(credit_transaction)

                print credit_transaction, float(self.__account.equity()), float(self.__account.available_funds())

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
                    AccountAction.DEBIT,
                    date,
                    amount,
                    currency,
                    (balance, benchmark_interest, rate, 'margin')
                    # 'Charge %.2f(%s) interest on %.2f margin' % (amount, currency, balance)
                )
                self.__account.add_transaction(transaction)

                print transaction, float(self.__account.equity()), float(self.__account.available_funds())

        for currency in [c for c in self.__account.fx_balance_currencies() if c != base_currency]:
            spread = Decimal(2.0)
            balance = self.__account.fx_balance(currency, previous_date)

            if balance < 0:
                benchmark_interest = [r for r in self.__interest_rates if r.code() == currency][0]
                rate = (benchmark_interest.immediate_rate(previous_date) + spread) / 100
                amount = balance * rate / days

                transaction = Transaction(
                    TransactionType.INTEREST,
                    AccountAction.DEBIT,
                    date,
                    abs(amount),
                    currency,
                    (balance, benchmark_interest, rate, 'balance')
                    # 'Charge %.2f(%s) interest on %.2f %s balance' % (abs(amount), currency, balance, currency)
                )
                self.__account.add_transaction(transaction)

                print transaction, float(self.__account.equity()), float(self.__account.available_funds())

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
                    AccountAction.CREDIT if amount > 0 else AccountAction.DEBIT,
                    date,
                    abs(amount),
                    currency,
                    (balance - minimums[currency], benchmark_interest, rate, 'balance')
                    # 'Pay %.2f(%s) interest (@ %.4f) on %.2f(%s) balance' % (amount, currency, rate, balance - minimums[currency], currency)
                )
                self.__account.add_transaction(transaction)

                print transaction, float(self.__account.equity()), float(self.__account.available_funds())
