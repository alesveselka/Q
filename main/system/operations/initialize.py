#!/usr/bin/python

import os
import sys
import json
import MySQLdb as mysql
import datetime as dt
from timer import Timer
from risk import Risk
from portfolio import Portfolio
from account import Account
from broker import Broker
from enum import Currency
from enum import Table
from enum import EventType
from enum import Interval
from investment_universe import InvestmentUniverse
from trading_model import TradingModel
from data_series import DataSeries
from persist import Persist
from report import Report
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
        trading_params = self.__simulation[Table.Simulation.TRADING_PARAMS]
        roll_strategy = self.__simulation[Table.Simulation.ROLL_STRATEGY_ID]

        precision = getcontext().prec
        risk_position_sizing = Decimal('%s' % params['risk_factor']).quantize(Decimal('1.' + ('0' * precision)))
        commission = (params['commission'], params['commission_currency'])
        interest_minimums = params['interest_minimums']

        now = dt.datetime.now()
        # end_date = dt.date(now.year, now.month, now.day)
        end_date = dt.date(1992, 6, 10)
        # end_date = dt.date(2015, 12, 31)
        timer = Timer()

        investment_universe = InvestmentUniverse(self.__simulation[Table.Simulation.INVESTMENT_UNIVERSE], self.__connection)
        investment_universe.load_data()
        self.__start_date = investment_universe.start_data_date()

        data_series = DataSeries(investment_universe, self.__connection)
        self.__futures = data_series.futures(params['slippage_map'])
        currency_pairs = data_series.currency_pairs()
        interest_rates = data_series.interest_rates()

        self.__account = Account(Decimal(params['initial_balance']), Currency.EUR, currency_pairs)
        self.__portfolio = Portfolio()

        risk = Risk(risk_position_sizing, self.__account)

        self.__broker = Broker(timer, self.__account, self.__portfolio, commission, currency_pairs, interest_rates, interest_minimums)
        trading_model = TradingModel(timer, self.__futures, risk, self.__portfolio, self.__broker)

        self.__load_and_calculate_data(self.__futures, currency_pairs, interest_rates, end_date)
        self.__start(timer, trading_model, end_date)
        # self.__on_timer_complete(end_date)

    def __start(self, timer, trading_system, end_date):
        """
        Start the system

        :param timer:           Timer instance
        :param trading_system:  TradingSystem instance
        :param end_date:        date of end of simulation
        """
        trading_system.subscribe()
        self.__broker.subscribe()
        timer.on(EventType.COMPLETE, self.__on_timer_complete)
        timer.start(self.__start_date, end_date)

    def __on_timer_complete(self, date):
        """
        Timer Complete event handler

        :param date:    date of the complete event
        """
        Persist(
            self.__connection,
            self.__start_date,
            date,
            self.__broker.order_results(),
            self.__account,
            self.__portfolio,
            self.__futures,
            self.__study_parameters()
        )

        report = Report(self.__account)
        # print '\n'.join(report.transactions(self.__start_date, date))
        print '\n'.join(report.to_lists(self.__start_date, date, Interval.MONTHLY))
        # report.to_lists(self.__start_date, date, Interval.MONTHLY)
        print '\n'.join(report.to_lists(self.__start_date, date))

    def __load_and_calculate_data(self, futures, currency_pairs, interest_rates, end_date):
        """
        Load data and calculate studies

        :param futures:         List of futures Market objects
        :param currency_pairs:  List of CurrencyPair instances
        :param interest_rates:  List of InterestRate instances
        :param end_date:        last date to load data
        """
        message = 'Loading Futures data ...'
        length = float(len(futures))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(futures))
        self.__log(message, complete=True)

        message = 'Calculating Futures studies ...'
        params = self.__study_parameters()
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].calculate_studies(params),
            enumerate(futures))
        self.__log(message, complete=True)

        message = 'Loading currency pairs data ...'
        length = float(len(currency_pairs))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(currency_pairs))
        self.__log(message, complete=True)

        message = 'Loading interest rates data ...'
        length = float(len(interest_rates))
        map(lambda i: self.__log(message, i[1].code(), i[0], length) and i[1].load_data(self.__connection, end_date),
            enumerate(interest_rates))
        self.__log(message, complete=True)

    def __study_parameters(self):
        """
        :return:    List of dictionaries with parameters for study calculations
        """
        studies = json.loads(self.__simulation[Table.Simulation.STUDIES])
        for s in studies:
            s['study'] = getattr(sys.modules['study'], s['study'])
            s['columns'] = [Table.Market.__dict__[c.upper()] for c in s['columns']]
        return studies

    def __simulation(self, name):
        """
        Fetches simulation data based on simulation name passed in
        
        :param name:    name of simulation data to return
        :return:        tuple representing record of requested simulation data
        """
        cursor = self.__connection.cursor()
        cursor.execute("SELECT * FROM `simulation` WHERE name = '%s'" % name)
        return cursor.fetchone()

    def __log(self, message, code='', index=0, length=0.0, complete=False):
        """
        Print message and percentage progress to console

        :param message:     Message to print
        :param index:       Index of the item being processed
        :param length:      Length of the whole range
        :param complete:    Flag indicating if the progress is complete
        :return:            boolean
        """
        sys.stdout.write('%s\r' % (' ' * 80))
        if complete:
            sys.stdout.write('%s complete\r\n' % message)
        else:
            sys.stdout.write('%s %s (%d of %d) [%d %%]\r' % (message, code, index, length, index / length * 100))
        sys.stdout.flush()
        return True
