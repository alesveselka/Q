#!/usr/bin/python

import sys
import json
from timer import Timer
from enum import Table
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
        self.__log('Saving orders')

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
        self.__log('Saving transactions')

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
        self.__log('Saving positions')

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
        self.__log('Saving studies')

        precision = 28
        markets_with_data = [m for m in markets if m.data()]
        length = float(len(markets_with_data))
        values = []
        for i, m in enumerate(markets_with_data):
            self.__log('Saving studies', i, length)

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

    def __save_equity(self, account, start_date, end_date):
        """
        Calculates equity, balances and margins and insert the values into DB

        :param account:     Account instance
        :param start_date:  start date to calculate from
        :param end_date:    end date to calculate to
        """
        self.__log('Saving equity')

        base_currency = account.base_currency()
        columns = ['base_currency', 'date', 'equity', 'balances', 'margins', 'margin_ratio']
        values = []
        date_range = Timer.daily_date_range(start_date, end_date)
        length = float(len(date_range))

        for i, date in enumerate(date_range):
            self.__log('Saving equity', i, length)

            equity = account.equity(date)
            margins = account.margin_loan_balances(date)
            total_margin = sum([account.base_value(v, k, date) for k, v in margins.items()])

            values.append((
                base_currency,
                date,
                self.__round(equity, 28),
                json.dumps({k: str(v) for k, v in account.fx_balances(date).items()}),
                json.dumps({k: str(v) for k, v in margins.items()}) if len(margins) else None,
                self.__round(total_margin / equity, 10) if total_margin else None
            ))

        self.__insert_values('equity', columns, values)

        self.__log('Saving equity', complete=True)

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

    def __round(self, value, precision):
        """
        Round Decimal value to specific precision

        :param value:       Decimal to round
        :param precision:   number of places in exponent
        :return:            rounded Decimal
        """
        try:
            result = value.quantize(Decimal('1.' + ('0' * precision))) if value else value
        except InvalidOperation:
            result = value
        return result

    def __log(self, message, index=1, length=1.0, complete=False):
        """
        Print message and percentage progress to console

        :param index:       Index of the item being processed
        :param length:      Length of the whole range
        :param complete:    Flag indicating if the progress is complete
        """
        sys.stdout.write('%s\r' % (' ' * 80))
        if complete:
            sys.stdout.write('%s complete\r\n' % message)
        else:
            sys.stdout.write('%s ... (%d of %d) [%s]\r' % (
                message,
                index,
                length,
                '{:.2%}'.format(index / length)
            ))
        sys.stdout.flush()
        return True
