#!/usr/bin/python


class Persist:

    def __init__(self, connection, orders, transactions, trades):
        self.__connection = connection
        self.__orders = orders
        self.__transactions = transactions
        self.__trades = trades

        self.__save_transactions()

    def __save_transactions(self):
        """
        Serialize and insert transaction objects into DB
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
