#!/usr/bin/python


class Persist:

    def __init__(self, connection, order_results, transactions, portfolio):
        self.__connection = connection
        self.__order_results = order_results
        self.__transactions = transactions
        self.__portfolio = portfolio

        # self.__save_orders()
        # self.__save_transactions()
        self.__save_positions()

    def __save_orders(self):
        """
        Serialize and insert Order instances into DB
        """
        self.__insert_values(
            'order',
            ['market_id', 'type', 'signal_type', 'date', 'price', 'quantity', 'result_type', 'result_price'],
            [
                (o.order().market().id(),
                 o.order().type(),
                 o.order().signal_type(),
                 o.order().date(),
                 o.order().price(),
                 o.order().quantity(),
                 o.type(),
                 o.price()
                 ) for o in self.__order_results]
        )

    def __save_transactions(self):
        """
        Serialize and insert Transaction instances into DB
        """
        self.__insert_values(
            'transaction',
            ['type', 'account_action', 'date', 'amount', 'currency', 'context'],
            [(t.type(), t.account_action(), t.date(), t.amount(), t.currency(), t.context_json()) for t in self.__transactions])

    def __save_positions(self):
        """
        Serialize and insert Position instances into DB
        """
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
                 p.enter_price(),
                 p.exit_date(),
                 p.exit_price(),
                 p.quantity(),
                 p.pnl(),
                 p.commissions()) for p in self.__portfolio.closed_positions() + self.__portfolio.open_positions()]
        )

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
