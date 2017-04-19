#!/usr/bin/python


class Persist:

    def __init__(self, connection, orders, transactions, trades):
        self.__connection = connection
        self.__orders = orders
        self.__transactions = transactions
        self.__trades = trades

    def save_orders(self):
        """
        Serialize and insert Order instances into DB
        """
        self.__insert_values(
            'order',
            ['market_id', 'type', 'date', 'price', 'quantity'],
            [(o.market().id(), o.type(), o.date(), o.price(), o.quantity()) for o in self.__orders]
        )

    def save_transactions(self):
        """
        Serialize and insert Transaction instances into DB
        """
        self.__insert_values(
            'transaction',
            ['type', 'account_action', 'date', 'amount', 'currency', 'context'],
            [(t.type(), t.account_action(), t.date(), t.amount(), t.currency(), t.context_json()) for t in self.__transactions])

    def save_trades(self):
        """
        Serialize and insert Trade instances into DB
        """
        self.__insert_values(
            'trade',
            [
                'market_id',
                'direction',
                'quantity',
                'enter_date',
                'enter_price',
                'enter_slip',
                'exit_date',
                'exit_price',
                'exit_slip',
                'commissions'
            ],
            [(
                 t.market().id(),
                 t.direction(),
                 t.quantity(),
                 t.enter_date(),
                 t.enter_price(),
                 t.enter_slip(),
                 t.exit_date(),
                 t.exit_price(),
                 t.exit_slip(),
                 t.commissions()) for t in self.__trades]
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
