#!/usr/bin/python

import json
import datetime as dt
from enum import Table
from collections import defaultdict
from decimal import Decimal, InvalidOperation


class Persist:

    def __init__(self, connection, start_date, end_date, order_results, account, portfolio, markets, study_parameters):
        self.__connection = connection

        self.__save_orders(order_results)
        self.__save_transactions(account.transactions(start_date, end_date))
        self.__save_positions(portfolio)
        self.__save_studies(markets, study_parameters)
        self.__save_equity(account, start_date, end_date)

    def __save_orders(self, order_results):
        """
        Serialize and insert Order instances into DB

        :param order_results:   list of OrderResult objects
        """
        precision = 10
        self.__insert_values(
            'order',
            ['market_id', 'type', 'signal_type', 'date', 'price', 'quantity', 'result_type', 'result_price'],
            [
                (o.order().market().id(),
                 o.order().type(),
                 o.order().signal_type(),
                 o.order().date(),
                 self.__round(o.order().price(), precision),
                 o.order().quantity(),
                 o.type(),
                 self.__round(o.price(), precision)
                 ) for o in order_results]
        )

    def __save_transactions(self, transactions):
        """
        Serialize and insert Transaction instances into DB

        :param transactions:    list of Transaction objects
        """
        precision = 28
        self.__insert_values(
            'transaction',
            ['type', 'account_action', 'date', 'amount', 'currency', 'context'],
            [(t.type(), t.account_action(), t.date(), self.__round(t.amount(), precision), t.currency(), t.context_json())
             for t in transactions]
        )

    def __save_positions(self, portfolio):
        """
        Serialize and insert Position instances into DB

        :param portfolio:   Portfolio object with references to lists of positions
        """
        precision = 10
        self.__insert_values(
            'position',
            [
                'market_id',
                'direction',
                'enter_date',
                'enter_price',
                'exit_date',
                'exit_price',
                'quantity',
                'pnl',
                'commissions'
            ],
            [(
                 p.market().id(),
                 p.direction(),
                 p.enter_date(),
                 self.__round(p.enter_price(), precision),
                 p.exit_date(),
                 self.__round(p.exit_price(), precision),
                 p.quantity(),
                 self.__round(p.pnl(), precision),
                 self.__round(p.commissions(), precision)
             ) for p in portfolio.closed_positions() + portfolio.open_positions()]
        )

    def __save_studies(self, markets, study_parameters):
        """
        Insert Study data into DB

        :param markets:             list of Market objects
        :param study_parameters:    list of Study parameters
        """
        precision = 28
        values = []
        for m in [m for m in markets if m.data()]:
            for p in study_parameters:
                study_data = m.study(p['name'])
                study_name = '_'.join([p['name'].split('_')[0], str(p['window'])])
                market_id = m.id()
                market_code = m.code()
                for d in study_data:
                    values.append((
                        study_name,
                        market_id,
                        market_code,
                        d[Table.Study.DATE],
                        self.__round(d[Table.Study.VALUE], precision),
                        self.__round(d[Table.Study.VALUE_2], precision) if len(d) > 2 else None
                    ))

        self.__insert_values('study', ['name', 'market_id', 'market_code', 'date', 'value', 'value_2'], values)

    def __insert_values(self, table_name, columns, values):
        """
        Insert values to the schema of name and columns passed in

        :param table_name:  Name of the table to insert data into
        :param columns:     list of column names to insert value into
        :param values:      list of values to insert
        """
        self.__connection.cursor().execute('DELETE FROM `%s`' % table_name)
        with self.__connection:
            cursor = self.__connection.cursor()
            cursor.executemany(
                'INSERT INTO `%s` (%s) VALUES (%s)' % (table_name, ','.join(columns), ('%s,' * len(columns))[:-1]),
                values
            )

    def __save_equity(self, account, start_date, end_date):
        """
        Calculates equity, balances and margins and insert the values into DB

        :param account:     Account instance
        :param start_date:  start date to calculate from
        :param end_date:    end date to calculate to
        """
        workdays = range(1, 6)
        daily_range = [start_date + dt.timedelta(days=i)
                       for i in xrange(0, (end_date - start_date).days + 1)
                       if (start_date + dt.timedelta(days=i)).isoweekday() in workdays]
        base_currency = account.base_currency()
        columns = ['base_currency', 'date', 'equity', 'balances', 'margins', 'margin_ratio']
        values = []

        for date in daily_range:
            equity = account.equity(date)
            balances = defaultdict(Decimal)
            for currency in account.fx_balance_currencies():
                balance = account.fx_balance(currency, date)
                if balance:
                    balances[currency] += balance

            margins = defaultdict(Decimal)
            total_margin = Decimal(0)
            for currency in account.margin_loan_currencies():
                margin = account.margin_loan_balance(currency, date)
                if margin:
                    margins[currency] += margin
                    total_margin += account.base_value(margin, currency, date)

            values.append((
                base_currency,
                date,
                self.__round(equity, 28),
                json.dumps({k: str(v) for k, v in balances.items()}),
                json.dumps({k: str(v) for k, v in margins.items()}) if len(margins) else None,
                self.__round(total_margin / equity, 10) if total_margin else None
            ))

        self.__insert_values('equity', columns, values)

    def __round(self, value, precision):
        """
        Round Decimal value to specific precision

        :param value:       Decimal to round
        :param precision:   number of places in exponent
        :return:            rounded Decimal
        """
        try:
            result = value.quantize(Decimal('1.' + ('0' * precision)))
        except InvalidOperation:
            result = value
        return result
