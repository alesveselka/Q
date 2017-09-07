#!/usr/bin/python

import json
from enum import Table
from operator import itemgetter
from collections import deque
from collections import defaultdict
from data.market_correlation import MarketCorrelationProxy
from abc import ABCMeta, abstractmethod


class MarketSeries(object):

    __metaclass__ = ABCMeta

    def __init__(self, start_data_date, study_parameters, roll_strategy, volatility_type, volatility_lookback, use_ew_correlation):
        self._start_data_date = start_data_date
        self._roll_strategy = roll_strategy
        self.__volatility_type = volatility_type
        self.__volatility_lookback = volatility_lookback
        self.__use_ew_correlation = use_ew_correlation

        self._prices = []
        self._price_indexes = {}

        self._correlations = []
        self._correlation_indexes = {}

        self.__study_parameters = study_parameters
        self.__studies = defaultdict(list)
        self.__study_data = {}
        self.__study_indexes = defaultdict(dict)
        self.__has_study_data = False

    def data(self, date):
        """
        Return market data at the date passed in

        :param date:    date of the required data
        :return:        tuple representing one day record
        """
        index = self._price_indexes[date] if date in self._price_indexes else None
        return (self._prices[index], self._prices[index-1]) if index else (None, None)

    def correlation(self, date):
        """
        Find and return series volatility to the date and correlation with the other market, which ID is passed in
        
        :param date:        date of the correlation record
        :return:            tuple(date, volatility number, and JSON(correlation dict))
        """
        index = self._correlation_indexes[date] if date in self._correlation_indexes else None
        return self._correlations[index] if index else [c for c in self._correlations if c[Table.MarketCorrelation.DATE] <= date][-1]

    def data_range(self, start_date, end_date):
        """
        Return data between the start and end date passed in
        
        :param start_date:  start date of the data
        :param end_date:    end date of the data
        :return:            list of data
        """
        return [d for d in self._prices if start_date <= d[Table.Market.PRICE_DATE] <= end_date]

    def study(self, study_name, date=None):
        """
        Return data of the study to the date passed in

        :param study_name:  Name of the study which data to return
        :param date:        last date of data required
        :return:            List of tuples - records of study specified
        """
        index = (self.__study_indexes[study_name][date] if date in self.__study_indexes[study_name] else None) \
            if date else len(self.__study_indexes[study_name]) - 1
        return self.__studies[study_name][index] if index > -1 else None

    def study_range(self, study_name, start_date, end_date):
        """
        Return study data within range of the dates passed in
        
        :param study_name:  name of the study to return
        :param start_date:  start date of the data range
        :param end_date:    end date of the data range
        :return:            list of tuple(date, value, value_2)
        """
        return [s for s in self.__studies[study_name] if start_date <= s[Table.Study.DATE] <= end_date]

    @abstractmethod
    def update_data(self, date):
        """
        Update dynamic data
        
        :param date:    date of the data update
        """
        raise NotImplementedError("Should implement 'update_data(date)'")

    def update_studies(self, date):
        """
        Update dynamic studies
        
        :param date:    date of the update
        """
        if date in self._price_indexes:
            index = self._price_indexes[date]
            market_data = self._prices[index]
            settle_price = market_data[Table.Market.SETTLE_PRICE]
            previous_settle = self._prices[index-1][Table.Market.SETTLE_PRICE] if index else settle_price
            volume = market_data[Table.Market.VOLUME]
            tr = max(market_data[Table.Market.HIGH_PRICE], previous_settle) - min(market_data[Table.Market.LOW_PRICE], previous_settle)
            study_data_keys = set('%s:%s' % (p['columns'][-1] if len(p['columns']) == 2 else 'tr', p['window']) for p in self.__study_parameters)
            l = locals()
            for key in study_data_keys:
                column, window = key.split(':')
                self.__study_data['%s_%s' % (column, window)].append(l[column])

            has_study = []
            for params in self.__study_parameters:
                window = params['window']
                study_type = params['study']
                study_name = params['name']
                study = self.__studies[study_name]
                data_columns = params['columns'][1:]
                column = data_columns[-1] if len(data_columns) == 1 else 'tr'
                study_data = self.__study_data['%s_%s' % (column, window)]

                if study_type == 'SMA':
                    study.append((date, sum(study_data) / len(study_data)))

                if study_type == 'EMA' or study_type == 'ATR':
                    c = 2.0 / (window + 1)
                    ma = study[-1][1] if len(study) else (sum(study_data) / len(study_data))
                    study.append((date, (c * l[column]) + (1 - c) * ma))

                if study_type == 'HHLL':
                    study.append((date, max(study_data), min(study_data)))

                self.__study_indexes[study_name][date] = len(study) - 1

                has_study.append(len(study) >= window)

            self.__has_study_data = all(has_study)

    def has_study_data(self):
        """
        Returns flag indicating if the market has studies data
        
        :return:    boolean
        """
        return self.__has_study_data

    def load(self, connection, end_date, delivery_months, market_id, market_code, roll_strategy_id):
        """
        Load series data

        :param connection:          MySQLdb connection instance
        :param end_date:            Last date to fetch data to
        :param delivery_months:     list of delivery months [(code, short-month-name)]
        :param market_id:           ID of the series market
        :param market_code:         code symbol of the series market
        :param roll_strategy_id:    ID of the series roll strategy
        """
        study_data_keys = set('%s:%s' % (p['columns'][-1] if len(p['columns']) == 2 else 'tr', p['window']) for p in self.__study_parameters)
        for key in study_data_keys:
            column, window = key.split(':')
            self.__study_data['%s_%s' % (column, window)] = deque([], int(window))

        # self._correlations, self._correlation_indexes = MarketCorrelationProxy.from_db(
        #     connection,
        #     market_id,
        #     market_code,
        #     self._start_data_date,
        #     end_date,
        #     self.__volatility_type,
        #     self.__volatility_lookback,
        #     self.__use_ew_correlation
        # )
        self._correlations, self._correlation_indexes = MarketCorrelationProxy.from_files(market_code, self._start_data_date, end_date)
        # MarketCorrelationProxy.dump(market_code, self._correlations)

    @abstractmethod
    def contract(self, date):
        """
        Return latest rolled-in contract code
        
        :return:    string code representing the latest rolled-in contract
        """
        raise NotImplementedError("Should implement 'contract()'")

    @abstractmethod
    def rolls(self):
        """
        Return contract rolls
        
        :return:    list of tuples(date, gap, roll-out-contract, roll-in-contract)
        """
        raise NotImplementedError("Should implement 'rolls()'")

    @abstractmethod
    def margin(self, end_date, point_value):
        """
        Return calculated margin based on price and point value at the date passed in
        
        :param end_date:    date to calculate margin on
        :param point_value: point value of the market instrument
        :return:            number representing margin
        """
        raise NotImplementedError("Should implement 'margin(end_date, point_value)'")

    def _column_names(self):
        """
        Construct and return column names sorted by their index in ENUM

        :return:    string
        """
        # TODO External 'Entity'?
        columns = {
            'code': Table.Market.CODE,
            'price_date': Table.Market.PRICE_DATE,
            'open_price': Table.Market.OPEN_PRICE,
            'high_price': Table.Market.HIGH_PRICE,
            'low_price': Table.Market.LOW_PRICE,
            'settle_price': Table.Market.SETTLE_PRICE,
            'volume': Table.Market.VOLUME
        }
        return ', '.join([i[0] for i in sorted(columns.items(), key=itemgetter(1))])
