#!/usr/bin/python

import datetime as dt
from math import ceil
from enum import Study
from enum import Table
from math import floor, log10


class Market:

    def __init__(self, market_id, slippage_map, series, name, code, data_codes, currency, tick_value, point_value, margin):
        self.__id = market_id
        self.__slippage_map = slippage_map
        self.__name = name
        self.__market_code = code
        self.__instrument_code = ''.join([code, '2']) if 'C' in data_codes else code
        self.__currency = currency
        self.__tick_value = tick_value
        self.__point_value = point_value
        self.__margin = margin
        self.__series = series

    def id(self):
        return self.__id

    def code(self):
        return self.__instrument_code

    def currency(self):
        return self.__currency

    def point_value(self):
        return self.__point_value

    def data(self, date):
        return self.__series.data(date)

    def correlation(self, date):
        return self.__series.correlation(date)

    def data_range(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        return self.__series.data_range(start_date, end_date)

    def study(self, study_name, date=None):
        return self.__series.study(study_name, date)

    def study_range(self, study_name, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        return self.__series.study_range(study_name, start_date, end_date)

    def update_data(self, date):
        self.__series.update_data(date)

    def update_studies(self, date):
        self.__series.update_studies(date)

    def has_study_data(self):
        return self.__series.has_study_data()

    def load_data(self, connection, end_date, delivery_months, roll_strategy_id):
        self.__series.load(connection, end_date, delivery_months, self.__id, self.__instrument_code, roll_strategy_id)

        if self.__margin == 0:
            self.__margin = self.__series.margin(end_date, self.__point_value)

        return True

    def contract(self, date):
        return self.__series.contract(date)

    def previous_contract(self, contract):
        return self.__series.previous_contract(contract)

    def next_contract(self, contract):
        return self.__series.next_contract(contract)

    def contract_data(self, contract, date):
        return self.__series.contract_data(contract, date)

    def contract_rolls(self):
        return self.__series.rolls()

    def margin(self):
        return self.__margin

    def slippage(self, date, quantity):
        """
        Calculates and returns 'slippage' in points
        (At minimum 1 tick)

        :param date:        date on which to calculate the slippage
        :param quantity:    number of contracts to open
        :return:            Number representing slippage in market points
        """
        atr = self.__series.study(Study.ATR_SHORT, date)[Table.Study.VALUE]
        volume = self.__series.study(Study.VOL_SHORT, date)[Table.Study.VALUE]
        atr_multiple = [s for s in self.__slippage_map if s['min'] <= volume < s['max']][0].get('atr')
        quantity_factor = 2 ** floor(log10(quantity))
        slippage_value = atr_multiple * atr
        result = (ceil(slippage_value / self.__tick_value) * self.__tick_value) / self.__point_value
        return result * quantity_factor
