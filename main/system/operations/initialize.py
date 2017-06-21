#!/usr/bin/python

import os
import json
import MySQLdb as mysql
from decimal import Decimal
from enum import Table
from account import Account
from broker import Broker
from data_series import DataSeries
from investment_universe import InvestmentUniverse
from portfolio import Portfolio
from risk import Risk
from simulate import Simulate
from trading_models.breakout_ma_filter_atr_stop import BreakoutMAFilterATRStop


class Initialize:

    def __init__(self, simulation_name):
        connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        simulation = self.__simulation(simulation_name, connection)
        params = json.loads(simulation[Table.Simulation.PARAMS])
        roll_strategy = self.__roll_strategy(simulation[Table.Simulation.ROLL_STRATEGY_ID], connection)

        base_currency = params['base_currency']
        commission_currency = params['commission_currency']
        commission = (params['commission'], commission_currency)
        interest_minimums = params['interest_minimums']

        investment_universe = InvestmentUniverse(simulation[Table.Simulation.INVESTMENT_UNIVERSE], connection)
        investment_universe.load_data()

        data_series = DataSeries(investment_universe, connection, simulation[Table.Simulation.STUDIES])
        futures = data_series.futures(roll_strategy[Table.RollStrategy.ID], params['slippage_map'])
        currency_pairs = data_series.currency_pairs(base_currency, commission_currency)
        interest_rates = data_series.interest_rates(base_currency, commission_currency)

        account = Account(Decimal(params['initial_balance']), base_currency, currency_pairs)
        broker = Broker(account, commission, currency_pairs, interest_rates, interest_minimums)
        trading_model = self.__trading_model(simulation[Table.Simulation.TRADING_MODEL])(
            futures,
            json.loads(simulation[Table.Simulation.TRADING_PARAMS]),
            roll_strategy
        )

        risk = Risk(params['risk_factor'], account)
        Simulate(simulation[Table.Simulation.ID], data_series, risk, account, broker, Portfolio(), trading_model)

    def __simulation(self, name, connection):
        """
        Fetches simulation data based on simulation name passed in
        
        :param name:    name of simulation data to return
        :return:        tuple representing record of requested simulation data
        """
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM `simulation` WHERE name = '%s'" % name)
        return cursor.fetchone()

    def __roll_strategy(self, roll_strategy_id, connection):
        """
        Fetch and return roll strategy by ID passed in
        
        :param roll_strategy_id:    ID of the strategy to return
        :return:                    tuple(name, type, params)
        """
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM `roll_strategy` WHERE id = '%s'" % roll_strategy_id)
        return cursor.fetchone()

    def __trading_model(self, name):
        """
        Find trend model class in the map by name and returns it
        
        :param name:    Name of the trading model
        :return:        Class of the treding model
        """
        return {
            'breakout_with_MA_filter_and_ATR_stop': BreakoutMAFilterATRStop
        }[name]
