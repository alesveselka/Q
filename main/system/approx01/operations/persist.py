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
        columns = ['market_id', 'type', 'date', 'price', 'quantity']
        values = [(o.market().id(), o.type(), o.date(), o.price(), o.quantity()) for o in self.__orders]

        self.__connection.cursor().execute('DELETE FROM `order`')
        with self.__connection:
            cursor = self.__connection.cursor()
            cursor.executemany(
                'INSERT INTO `order` (%s) VALUES (%s)' % (','.join(columns), ('%s,' * len(columns))[:-1]),
                values
            )

    def save_transactions(self):
        """
        Serialize and insert Transaction instances into DB
        """
        columns = ['type', 'account_action', 'date', 'amount', 'currency', 'context']
        values = [(t.type(), t.account_action(), t.date(), t.amount(), t.currency(), t.context_json())
                  for t in self.__transactions]

        self.__connection.cursor().execute('DELETE FROM `transaction`')
        with self.__connection:
            cursor = self.__connection.cursor()
            cursor.executemany(
                'INSERT INTO `transaction` (%s) VALUES (%s)' % (','.join(columns), ('%s,' * len(columns))[:-1]),
                values
            )

    def save_trades(self):
        """
        Serialize and insert Trade instances into DB
        """
        columns = [
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
        ]
        values = [(
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

        self.__connection.cursor().execute('DELETE FROM `trade`')
        with self.__connection:
            cursor = self.__connection.cursor()
            cursor.executemany(
                'INSERT INTO `trade` (%s) VALUES (%s)' % (','.join(columns), ('%s,' * len(columns))[:-1]),
                values
            )
