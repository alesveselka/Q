#!/usr/bin/python

import datetime as dt
from collections import defaultdict


class MarketSeries:

    def __init__(self):
        self.__start_data_date = start_data_date
        self.__roll_strategy_id = roll_strategy_id
        self.__adjusted_data = []
        self.__data_indexes = {}
        self.__contracts = defaultdict(list)
        self.__contract_rolls = []
        self.__roll_schedule = []
        self.__scheduled_rolls = []
        self.__actual_rolls = []
        self.__studies = {}
        self.__study_indexes = {}
        self.__first_study_date = dt.date(9999, 12, 31)
        self.__has_study_data = False

        self.__dynamic_data = []
        self.__dynamic_indexes = {}
        self.__dynamic_studies = defaultdict(list)
        self.__dynamic_study_data = {}
        self.__dynamic_study_indexes = defaultdict(dict)

    def data(self, date):
        """
        Return market data at the date passed in

        :param date:    date of the required data
        :return:        tuple representing one day record
        """
        # index = self.__data_indexes[date] if date in self.__data_indexes else None
        # return (self.__adjusted_data[index], self.__adjusted_data[index-1]) if index else (None, None)
        index = self.__dynamic_indexes[date] if date in self.__dynamic_indexes else None
        return (self.__dynamic_data[index], self.__dynamic_data[index-1]) if index else (None, None)

    def data_range(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Return data between the start and end date passed in
        
        :param start_date:  start date of the data
        :param end_date:    end date of the data
        :return:            list of data
        """
        return [d for d in self.__dynamic_data if start_date <= d[Table.Market.PRICE_DATE] <= end_date]
