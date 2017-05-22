#!/usr/bin/python

import os
import json
import MySQLdb as mysql
from risk import Risk
from portfolio import Portfolio
from account import Account
from broker import Broker
from enum import Currency
from enum import Table
from investment_universe import InvestmentUniverse
from trading_model import TradingModel
from data_series import DataSeries
from simulate import Simulate
from decimal import Decimal, getcontext


class Initialize:

    def __init__(self, simulation_name):
        self.__connection = mysql.connect(
            os.environ['DB_HOST'],
            os.environ['DB_USER'],
            os.environ['DB_PASS'],
            os.environ['DB_NAME']
        )
        self.__simulation = self.__simulation(simulation_name)
        params = json.loads(self.__simulation[Table.Simulation.PARAMS])
        trading_model_id = self.__simulation[Table.Simulation.TRADING_MODEL_ID]
        roll_strategy = self.__simulation[Table.Simulation.ROLL_STRATEGY_ID]

        precision = getcontext().prec
        risk_position_sizing = Decimal('%s' % params['risk_factor']).quantize(Decimal('1.' + ('0' * precision)))
        commission = (params['commission'], params['commission_currency'])
        interest_minimums = params['interest_minimums']

        investment_universe = InvestmentUniverse(self.__simulation[Table.Simulation.INVESTMENT_UNIVERSE], self.__connection)
        investment_universe.load_data()
        self.__start_date = investment_universe.start_data_date()

        data_series = DataSeries(investment_universe, self.__connection, self.__simulation[Table.Simulation.STUDIES])
        self.__futures = data_series.futures(params['slippage_map'])
        currency_pairs = data_series.currency_pairs()
        interest_rates = data_series.interest_rates()

        self.__account = Account(Decimal(params['initial_balance']), Currency.EUR, currency_pairs)
        self.__portfolio = Portfolio()

        risk = Risk(risk_position_sizing, self.__account)

        self.__broker = Broker(self.__account, commission, currency_pairs, interest_rates, interest_minimums)
        trading_model = TradingModel(self.__futures, risk, json.loads(self.__simulation[Table.Simulation.TRADING_PARAMS]))

        Simulate(data_series, risk, self.__account, self.__broker, self.__portfolio, trading_model)

    def __simulation(self, name):
        """
        Fetches simulation data based on simulation name passed in
        
        :param name:    name of simulation data to return
        :return:        tuple representing record of requested simulation data
        """
        cursor = self.__connection.cursor()
        cursor.execute("SELECT * FROM `simulation` WHERE name = '%s'" % name)
        return cursor.fetchone()
