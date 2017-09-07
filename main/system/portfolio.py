#!/usr/bin/python

import json
from math import log
from operator import mul
from itertools import combinations
from collections import defaultdict
from enum import Table


class Portfolio(object):

    def __init__(self, account, volatility_target, use_correlation_weights):
        self.__account = account
        self.__volatility_target = volatility_target
        self.__use_correlation_weights = use_correlation_weights
        self.__positions = []
        self.__closed_positions = []

    def add_position(self, position):
        self.__positions.append(position)

    def remove_position(self, position):
        self.__closed_positions.append(position)
        self.__positions.remove(position)

    def market_position(self, market):
        positions = [p for p in self.__positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None

    def open_positions(self):
        return self.__positions

    def closed_positions(self):
        return self.__closed_positions

    def candidate(self, date):
        equity = float(self.__account.equity(date))
        cash_volatility_target = equity * self.__volatility_target
        daily_cash_volatility_target = cash_volatility_target / 16
        print date, equity, cash_volatility_target, daily_cash_volatility_target
        # self.__correlation_weights(date)
        self.__volatility_scalars(date, daily_cash_volatility_target)
        self.__diversification_multiplier(date)

    def __correlation_weights(self, date):
        # TODO The 'Handcrafting' method assumes the assets have the same expected standard deviation of returns!
        # TODO also incorporate new orders and create DIFF
        markets = [p.market() for p in self.__positions]
        if len(markets) >= 2:
            market_ids = {str(m.id()): m for m in markets}
            pairs = list(combinations(market_ids.keys(), 2))
            groups = defaultdict(list)
            market_correlations = defaultdict(list)
            group_correlations = defaultdict(list)
            fraction = .25
            print date, market_ids.keys(), pairs
            for pair in pairs:
                correlation_data = market_ids[pair[0]].correlation(date)
                volatility = correlation_data[Table.MarketCorrelation.VOLATILITY]
                correlation = json.loads(correlation_data[Table.MarketCorrelation.CORRELATIONS])[pair[1]]
                correlation = 1e-6 if correlation == 0.0 else abs(correlation)
                market_correlations[pair[0]].append(correlation)
                market_correlations[pair[1]].append(correlation)
                rounded_correlation = (fraction * round(correlation/fraction)) if correlation else None
                group_correlations[pair[0]].append(rounded_correlation)
                group_correlations[pair[1]].append(rounded_correlation)
                groups[rounded_correlation].append({pair: round(correlation, 2)})
                print pair, round(correlation, 2), rounded_correlation, volatility

            # print date, market_correlations, group_correlations
            for k in market_correlations.keys():
                print k, market_correlations[k], reduce(mul, market_correlations[k]), log(reduce(mul, market_correlations[k]))

            # TODO if there is only one group, no need to calculate average AND not need to use group at first place
            if len(group_correlations) <= 1:
                for k in group_correlations.keys():
                    print k, group_correlations[k], sum(group_correlations[k]) / len(group_correlations[k]), log(sum(group_correlations[k]) / len(group_correlations[k]))

    def __volatility_scalars(self, date, daily_cash_volatility_target):
        markets = [p.market() for p in self.__positions]
        for market in markets:
            market_data, previous_data = market.data(date)
            data = previous_data if previous_data else market.data_range(end_date=date)[-1]
            price_date = data[Table.Market.PRICE_DATE]
            price = data[Table.Market.SETTLE_PRICE]
            point_value = market.point_value()
            block_value = price * point_value
            correlation_data = market.correlation(price_date)
            price_volatility = correlation_data[Table.MarketCorrelation.VOLATILITY]
            instrument_currency_volatility = price_volatility * block_value
            instrument_value_volatility = self.__account.base_value(instrument_currency_volatility, market.currency(), price_date)
            volatility_scalar = daily_cash_volatility_target / instrument_value_volatility
            print market.code(), int(daily_cash_volatility_target), price, point_value, block_value, price_volatility, instrument_currency_volatility, instrument_value_volatility, volatility_scalar

    def __diversification_multiplier(self, date):
        return 1.0
