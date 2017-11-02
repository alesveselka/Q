#!/usr/bin/python

import os
import sys
import json
import datetime as dt
import MySQLdb as mysql
from timer import Timer
from enum import Table
from enum import TransactionType
from decimal import Decimal, InvalidOperation


class Persist:

    def __init__(self, simulation_id, roll_strategy, start_date, end_date, account, broker, data_series):
        self.__connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        roll_strategy_id = roll_strategy[Table.RollStrategy.ID]
        roll_strategy_name = roll_strategy[Table.RollStrategy.NAME]
        futures = data_series.futures(None, None, None, None, None, None)

        # self.__save_trades(simulation_id, broker.trades(start_date, end_date))
        # self.__save_transactions(simulation_id, account.transactions(start_date, end_date))
        # self.__save_positions(simulation_id, broker, start_date, end_date)
        # self.__save_studies(simulation_id, futures, data_series.study_parameters())
        # self.__save_equity(simulation_id, account, start_date, end_date)
        # self.__save_market_equity(simulation_id, account, broker, futures, start_date, end_date)

        # self.__save_price_series(simulation_id, roll_strategy_id, roll_strategy_name, futures)

    def __save_trades(self, simulation_id, trades):
        """
        Serialize and insert Order instances into DB

        :param int simulation_id:   ID of the simulation
        :param list trades:         list of Trade objects
        """
        self.__log('Saving trades')

        values = []
        for trade in trades:
            order = trade.order()
            result = trade.result()

            values.append((
                simulation_id,
                order.market().id(),
                order.contract(),
                order.date(),
                order.price(),
                order.quantity(),
                result.type(),
                result.price(),
                result.quantity()
            ))

        self.__insert_values(
            'trade',
            'simulation_id',
            simulation_id,
            [
                'simulation_id',
                'market_id',
                'contract',
                'date',
                'order_price',
                'order_quantity',
                'result_type',
                'result_price',
                'result_quantity'
            ], values
        )

    def __save_transactions(self, simulation_id, transactions):
        """
        Serialize and insert Transaction instances into DB

        :param simulation_id:   ID of the simulation
        :param transactions:    list of Transaction objects
        """
        self.__log('Saving transactions')

        precision = 28
        self.__insert_values(
            'transaction',
            'simulation_id',
            simulation_id,
            ['simulation_id', 'type', 'account_action', 'date', 'amount', 'currency', 'context'],
            [(
                simulation_id,
                t.type(),
                t.account_action(),
                t.date(),
                self.__round(t.amount(), precision) if isinstance(t.amount(), Decimal) else t.amount(),
                t.currency(),
                t.context_json()) for t in transactions]
        )

    def __save_positions(self, simulation_id, broker, start_date, end_date):
        """
        Save market positions into DB
        
        :param int simulation_id:   ID of the simulation
        :param Broker broker:       Broker object
        :param date start_date:     starting date of the simulation
        :param date end_date:       end date of the simulation
        """
        self.__log('Saving positions')

        columns = ['simulation_id', 'date', 'positions']
        values = []
        date_range = Timer.daily_date_range(start_date, end_date)
        length = float(len(date_range))

        for i, date in enumerate(date_range):
            self.__log('Saving positions', i, length)
            values.append((simulation_id, date, self.__json(broker.positions(date))))

        self.__insert_values('positions', 'simulation_id', simulation_id, columns, values)

        self.__log('Saving positions', complete=True)

        # TODO also save individual positions in time?
        # precision = 10
        # self.__insert_values(
        #     'position',
        #     'simulation_id',
        #     simulation_id,
        #     [
        #         'simulation_id',
        #         'market_id',
        #         'direction',
        #         'contract',
        #         'enter_date',
        #         'enter_price',
        #         'exit_date',
        #         'exit_price',
        #         'quantity',
        #         'pnl',
        #         'commissions'
        #     ],
        #     [(
        #          simulation_id,
        #          p.market().id(),
        #          p.direction(),
        #          p.contract(),
        #          p.enter_date(),
        #          p.enter_price(),
        #          p.exit_date(),
        #          p.exit_price(),
        #          p.order_results()[0].quantity(),  # TODO quantity change in time now
        #          p.pnl(),
        #          self.__round(p.commissions(), precision)
        #      ) for p in portfolio.closed_positions() + portfolio.open_positions()]
        # )

    # TODO 'simulation_id' is not used
    def __save_price_series(self, simulation_id, roll_strategy_id, roll_strategy_name, markets):
        """
        Persist continuous adjusted price series of the markets passed in
        
        :param simulation_id:       ID of the simulation
        :param roll_strategy_id:    ID of the roll strategy
        :param roll_strategy_name:  name of the roll strategy
        :param markets:             markets of which price series to persist
        """
        self.__log('Saving price series')

        if roll_strategy_name != 'norgate':
            now = dt.datetime.now()
            price_columns = [
                'market_id',
                'roll_strategy_id',
                'code',
                'price_date',
                'open_price',
                'high_price',
                'low_price',
                'last_price',
                'settle_price',
                'volume',
                'open_interest',
                'created_date',
                'last_updated_date'
            ]
            roll_columns = [
                'market_id',
                'roll_strategy_id',
                'date',
                'gap',
                'roll_out_contract',
                'roll_in_contract'
            ]
            length = float(len(markets))
            price_values = []
            roll_values = []
            for i, m in enumerate(markets):
                self.__log('Saving price series', i, length)

                market_id = m.id()
                market_code = m.code()
                price_values += [(
                    market_id,
                    roll_strategy_id,
                    market_code,
                    d[Table.Market.PRICE_DATE],
                    d[Table.Market.OPEN_PRICE],
                    d[Table.Market.HIGH_PRICE],
                    d[Table.Market.LOW_PRICE],
                    d[Table.Market.SETTLE_PRICE],
                    d[Table.Market.SETTLE_PRICE],
                    d[Table.Market.VOLUME],
                    0,
                    now,
                    now
                ) for d in m.data_range()]

                roll_values += [(
                    market_id,
                    roll_strategy_id,
                    r[Table.ContractRoll.DATE],
                    r[Table.ContractRoll.GAP],
                    r[Table.ContractRoll.ROLL_OUT_CONTRACT],
                    r[Table.ContractRoll.ROLL_IN_CONTRACT]
                ) for r in m.contract_rolls()]

            self.__insert_values('continuous_adjusted', 'roll_strategy_id', roll_strategy_id, price_columns, price_values)
            self.__insert_values('contract_roll', 'roll_strategy_id', roll_strategy_id, roll_columns, roll_values)

    def __save_studies(self, simulation_id, markets, study_parameters):
        """
        Insert Study data into DB

        :param simulation_id:       ID of the simulation
        :param markets:             list of Market objects
        :param study_parameters:    list of Study parameters
        """
        self.__log('Saving studies')

        length = float(len(markets))
        values = []
        for i, m in enumerate(markets):
            self.__log('Saving studies', i, length)

            for p in study_parameters:
                study_name = p['name']
                try:
                    study_data = m.study_range(study_name)
                    market_id = m.id()
                    market_code = m.code()
                    for d in study_data:
                        values.append((
                            simulation_id,
                            study_name,
                            market_id,
                            market_code,
                            d[Table.Study.DATE],
                            d[Table.Study.VALUE],
                            d[Table.Study.VALUE_2] if len(d) > 2 else None
                        ))
                except KeyError:
                    continue

        self.__insert_values(
            'study',
            'simulation_id',
            simulation_id,
            ['simulation_id', 'name', 'market_id', 'market_code', 'date', 'value', 'value_2'],
            values
        )

    def __save_equity(self, simulation_id, account, start_date, end_date):
        """
        Calculates equity, balances and margins and insert the values into DB

        :param simulation_id:   ID of the simulation
        :param account:         Account instance
        :param start_date:      start date to calculate from
        :param end_date:        end date to calculate to
        """
        self.__log('Saving equity')

        columns = [
            'simulation_id',
            'date',
            'equity',
            'available_funds',
            'balances',
            'margins',
            'marked_to_market',
            'commissions',
            'fx_translations',
            'margin_interest',
            'balance_interest',
            'rates',
            'margin_ratio'
        ]
        values = []
        date_range = Timer.daily_date_range(start_date, end_date)
        length = float(len(date_range))

        for i, date in enumerate(date_range):
            self.__log('Saving equity', i, length)

            equity = account.equity(date)
            funds = account.available_funds(date)
            margins = account.margin_loan_balances(date)
            total_margin = sum(account.base_value(v, k, date) for k, v in margins.items())

            transactions = account.transactions(date, date, True)
            marked_to_market = account.aggregate(transactions, [TransactionType.MTM_TRANSACTION, TransactionType.MTM_POSITION])
            commissions = account.aggregate(transactions, [TransactionType.COMMISSION])
            fx_translations = account.aggregate(transactions, [TransactionType.FX_BALANCE_TRANSLATION])
            margin_interest = account.aggregate(transactions, [TransactionType.MARGIN_INTEREST])
            balance_interest = account.aggregate(transactions, [TransactionType.BALANCE_INTEREST])

            values.append((
                simulation_id,
                date,
                self.__round(equity, 28),
                self.__round(funds, 28),
                self.__json(account.fx_balances(date)),
                self.__json(margins),
                self.__json(marked_to_market),
                self.__json(commissions),
                self.__json(fx_translations),
                self.__json(margin_interest),
                self.__json(balance_interest),
                self.__json(account.rates(date)),
                total_margin / float(equity) if total_margin else None
            ))

        self.__insert_values('equity', 'simulation_id', simulation_id, columns, values)

        self.__log('Saving equity', complete=True)

    def __save_market_equity(self, simulation_id, account, broker, markets, start_date, end_date):
        """
        Calculates equity, balances and margins and insert the values into DB

        :param int simulation_id:   ID of the simulation
        :param Account account:     Account instance
        :param Broker broker:       Broker instance
        :param list markets:        list of markets
        :param date start_date:     start date to calculate from
        :param date end_date:       end date to calculate to
        """
        self.__log('Saving market equity')

        mtm_types = [TransactionType.MTM_TRANSACTION, TransactionType.MTM_POSITION]
        comm_types = [TransactionType.COMMISSION]
        columns = [
            'simulation_id',
            'market_id',
            'contract',
            'date',
            'equity',
            'marked_to_market',
            'commissions',
            'positions'
        ]
        values = []
        date_range = Timer.daily_date_range(start_date, end_date)
        length = float(len(date_range))

        for i, date in enumerate(date_range):
            self.__log('Saving market positions', i, length)

            transactions = account.transactions(date, date, True)
            mtm_transactions = [t for t in transactions if t.type() in mtm_types]
            comm_transactions = [t for t in transactions if t.type() in comm_types]
            positions = broker.positions(date)

            for market in markets:
                market_data, _ = market.data(date)
                if market_data:
                    market_id = market.id()
                    market_positions = {k.split('_')[1]: positions[k] for k in positions.keys() if k.split('_')[0] == str(market_id)}
                    market_position = market_positions.items()[0] if len(market_positions) else None
                    position_contract = market_position[0] if market_position and market_position[0] != 'None' else None
                    position_quantity = market_position[1] if market_position else 0
                    market_mtm_transactions = [t for t in mtm_transactions if t.context()[0].id() == market_id]
                    market_comm_transactions = [t for t in comm_transactions if t.context()[0].id() == market_id]
                    mtm = account.aggregate(market_mtm_transactions, mtm_types)
                    mtm = sum(account.base_value(mtm[c], c, date) for c in mtm.keys())
                    commissions = account.aggregate(market_comm_transactions, comm_types)
                    commissions = sum(account.base_value(commissions[c], c, date) for c in commissions.keys())
                    equity = mtm + commissions

                    values.append((
                        simulation_id,
                        market_id,
                        position_contract,
                        date,
                        equity,
                        mtm,
                        commissions,
                        position_quantity
                    ))

        self.__insert_values('market_equity', 'simulation_id', simulation_id, columns, values)

        self.__log('Saving market equity', complete=True)

    def __json(self, dictionary):
        """
        Serialize dicts into JSON
        
        :param dictionary:  dict to serialize
        :return:            JSON
        """
        return json.dumps({k: str(v) for k, v in dictionary.items()}) if len(dictionary) else None

    def __insert_values(self, table_name, delete_condition, delete_value, columns, values):
        """
        Insert values to the schema of name and columns passed in

        :param table_name:          Name of the table to insert data into
        :param delete_condition:    Name of the column to check when deleting
        :param delete_value:        Value of the delete clause to evaluate
        :param columns:             list of column names to insert value into
        :param values:              list of values to insert
        """
        self.__connection.cursor().execute("DELETE FROM `%s` WHERE `%s` = '%s'" % (table_name, delete_condition, delete_value))
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
