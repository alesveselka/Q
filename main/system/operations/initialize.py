#!/usr/bin/python

import os
import json
import time
import MySQLdb as mysql
from decimal import Decimal
from enum import Table
from enum import CapitalCorrection
from account import Account
from broker import Broker
from series.data_series import DataSeries
from investment_universe import InvestmentUniverse
from risk import Risk
from simulate import Simulate
from trading_models.breakout_ma_filter_atr_stop import BreakoutMAFilterATRStop
from trading_models.plunge_atr_stop_profit import PlungeATRStopProfit
from trading_models.bollinger_bands import BollingerBands
from trading_models.ma_trend_pullback import MATrendOnPullback
from trading_models.buy_and_hold import BuyAndHold
from trading_models.ewmac import EWMAC
from trading_models.carry import CARRY


class Initialize:

    def __init__(self, simulation_name):
        start_time = time.time()
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

        position_sizing = params['position_sizing']
        data_series = DataSeries(investment_universe, connection, json.loads(simulation[Table.Simulation.STUDIES]))
        futures = data_series.futures(params['slippage_map'], roll_strategy, position_sizing, *self.__correlation_data_params(params))
        currency_pairs = data_series.currency_pairs(base_currency, commission_currency)
        interest_rates = data_series.interest_rates(base_currency, commission_currency)

        start_data_date = investment_universe.start_data_date()
        account = Account(Decimal(params['initial_balance']), start_data_date, base_currency, currency_pairs)
        broker = Broker(account, commission, interest_rates, interest_minimums, params['sweep_fx_rule'], {f.id(): f for f in futures})
        trading_params = self.__trading_params(params, simulation[Table.Simulation.TRADING_PARAMS])
        trading_model = self.__trading_model(simulation[Table.Simulation.TRADING_MODEL])(
            simulation[Table.Simulation.NAME],
            futures,
            trading_params
        )

        Simulate(
            simulation,
            roll_strategy,
            data_series,
            Risk(account, position_sizing, *self.__position_sizing_params(params, trading_params)),
            account,
            broker,
            trading_model,
            params['position_inertia'],
            params['use_position_inertia']
        )

        print 'Time:', time.time() - start_time, (time.time() - start_time) / 60

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

    def __correlation_data_params(self, params):
        """
        Construct and return dict with correlation data pulled from params passed in, 
        optionally defaulted to hard-coded values
        
        :param params:  dict with loaded params
        :return:        dict with correlation-date related params
        """
        return (
            params.get('volatility_type', 'movement'),
            params.get('volatility_lookback', 25),
            params.get('use_ew_correlation', True),
        )

    def __position_sizing_params(self, params, trading_params):
        """
        Construct and return tuple with position sizing data pulled from params passed in, 
        optionally defaulted to hard-coded values
        
        :param params:          dict with loaded params
        :param trading_params:  dict with loaded trading-related params
        :return:                tuple with position sizing and risk related params
        """
        return (
            params.get('risk_factor', 0.002),
            params.get('volatility_target', 0.2),
            params.get('use_group_correlation_weights', False),
            params.get('capital_correction', CapitalCorrection.FULL_COMPOUNDING),
            params.get('partial_compounding_factor', 0.25),
            trading_params.get('forecast_const', 10.0)
        )

    def __trading_params(self, params, trading_params):
        """
        Return combination of trading params and params
        
        :param dict params:             general parameters
        :param string trading_params:   trading-related parameters as JSON string
        :return dict: 
        """
        return dict(json.loads(trading_params).items() + {
            'rebalance_interval': params.get('rebalance_interval', None),
            'roll_lookout_days': 7,
        }.items())

    def __trading_model(self, name):
        """
        Find trend model class in the map by name and returns it
        
        :param name:    Name of the trading model
        :return:        Class of the treding model
        """
        return {
            'breakout_with_MA_filter_and_ATR_stop': BreakoutMAFilterATRStop,
            'plunge_with_ATR_stop_and_profit': PlungeATRStopProfit,
            'bollinger_bands': BollingerBands,
            'ma_trend_on_pullback': MATrendOnPullback,
            'buy_and_hold': BuyAndHold,
            'ewmac': EWMAC,
            'carry': CARRY
        }[name]
