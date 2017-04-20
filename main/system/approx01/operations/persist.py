#!/usr/bin/python

from enum import Table
from decimal import Decimal, ROUND_HALF_EVEN


class Persist:

    def __init__(self, connection, order_results, transactions, portfolio, markets, study_parameters):
        # TODO no need to save - pass in
        self.__connection = connection
        self.__order_results = order_results
        self.__transactions = transactions
        self.__portfolio = portfolio

        # self.__save_orders()
        # self.__save_transactions()
        # self.__save_positions()
        self.__save_studies(markets, study_parameters)

    def __save_orders(self):
        """
        Serialize and insert Order instances into DB
        """
        exponent = Decimal('1.' + ('0' * 10))
        self.__insert_values(
            'order',
            ['market_id', 'type', 'signal_type', 'date', 'price', 'quantity', 'result_type', 'result_price'],
            [
                (o.order().market().id(),
                 o.order().type(),
                 o.order().signal_type(),
                 o.order().date(),
                 o.order().price().quantize(exponent),
                 o.order().quantity(),
                 o.type(),
                 o.price().quantize(exponent)
                 ) for o in self.__order_results]
        )

    def __save_transactions(self):
        """
        Serialize and insert Transaction instances into DB
        """
        exponent = Decimal('1.' + ('0' * 30))
        self.__insert_values(
            'transaction',
            ['type', 'account_action', 'date', 'amount', 'currency', 'context'],
            [(t.type(), t.account_action(), t.date(), t.amount().quantize(exponent), t.currency(), t.context_json()) for t in self.__transactions]
        )

    def __save_positions(self):
        """
        Serialize and insert Position instances into DB
        """
        exponent = Decimal('1.' + ('0' * 10))
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
                 p.enter_price().quantize(exponent),
                 p.exit_date(),
                 p.exit_price().quantize(exponent),
                 p.quantity(),
                 p.pnl().quantize(exponent),
                 p.commissions().quantize(exponent)
             ) for p in self.__portfolio.closed_positions() + self.__portfolio.open_positions()]
        )

    def __save_studies(self, markets, study_parameters):
        """
        Insert Study data into DB

        :param markets:             list of Market objects
        :param study_parameters:    list of Study parameters
        """
        exponent = Decimal('1.' + ('0' * 30))
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
                        d[Table.Study.VALUE].quantize(exponent),
                        d[Table.Study.VALUE_2].quantize(exponent) if len(d) > 2 else None
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
