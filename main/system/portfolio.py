#!/usr/bin/python

import json
from math import log
from math import sqrt
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

        markets = [p.market() for p in self.__positions]
        if len(markets):
            price_date = date
            prices = {}
            correlation_data = {}
            for market in markets:
                market_data, previous_data = market.data(date)
                data = previous_data if previous_data else market.data_range(end_date=date)[-1]
                price_date = data[Table.Market.PRICE_DATE]
                prices[market.id()] = data[Table.Market.SETTLE_PRICE]
                correlation_data[market.id()] = market.correlation(price_date)

            correlations, market_weights = self.__correlation_weights(correlation_data)
            volatility = self.__volatility_scalars(price_date, prices, correlation_data, daily_cash_volatility_target)

            # volatility = {1: (0.00625, 10), 2: (0.00625, 10)}
            # correlations = {('1', '2'): -0.6}
            # market_weights = {'1': 0.5, '2': 0.5}

            dm = self.__diversification_multiplier(volatility, correlations, market_weights)
            for market_id in volatility.keys():
                w = market_weights[market_id] if len(market_weights) else 1.0
                print \
                    market_id, \
                    volatility[market_id][1], \
                    w, \
                    dm, \
                    round(volatility[market_id][1] * w * dm, 2)  # final position!

    def __correlation_weights(self, correlation_data):
        """
        Calculate weights for each market based on correlations
        
        1. For each market, sum correlations with every other market;
        2. group market correlations and also sum these as 'group_weights';
        3. final weight for each market equals 'log(market correlations ^ group correlations) / sum of all correlations'
        
        :param correlation_data:    dict of market ID as a key and record from 'market_correlation' as a value
        :return:                    tuple of
                                        dict of market correlations with market IDs as keys, and
                                        dict of correlation weights for each market with market IDs as keys
        """
        # TODO The 'Handcrafting' method assumes the assets have the same expected standard deviation of returns!
        market_ids = correlation_data.keys()
        correlations = {}
        market_weights = {}
        if len(market_ids) >= 2:
            pairs = list(combinations(market_ids, 2))
            market_correlations = defaultdict(list)
            group_correlations = defaultdict(list)
            fraction = .25
            for pair in pairs:
                pair_1_id = pair[0]
                pair_2_id = pair[1]
                correlation = json.loads(correlation_data[pair_1_id][Table.MarketCorrelation.CORRELATIONS])[str(pair_2_id)]
                correlations[pair] = correlation
                correlation = 1e-6 if correlation == 0.0 else abs(correlation)
                market_correlations[pair_1_id].append(correlation)
                market_correlations[pair_2_id].append(correlation)
                rounded_correlation = (fraction * round(correlation / fraction)) if correlation else None
                group_correlations[pair_1_id].append(rounded_correlation)
                group_correlations[pair_2_id].append(rounded_correlation)

            group_weights = {}
            for market_id in market_ids:
                avg = sum(group_correlations[market_id]) / len(group_correlations[market_id])
                ln = log(avg) if avg else log(1e-6)
                ln = 1-1e-6 if avg == 1.0 else ln
                group_weights[market_id] = ln

            logs = sum(group_weights[k] for k in market_ids)
            group_weights = {k: group_weights[k] / logs for k in market_ids}

            market_weights = {m: reduce(mul, market_correlations[m]) for m in market_ids}
            group_logs = sum(log(market_weights[k]**group_weights[k]) for k in market_ids)
            market_weights = {m: log(market_weights[m]**group_weights[m]) / group_logs for m in market_ids}

        return correlations, market_weights

    def __volatility_scalars(self, date, prices, correlation_data, daily_cash_volatility_target):
        """
        Calculate price volatility and volatility scalars for each market
        
        :param date:                            date on which to calculate
        :param prices:                          dict of prices and their respective market IDs as keys
        :param correlation_data:                dict of market ID as a key and record from 'market_correlation' as a value
        :param daily_cash_volatility_target:    equity x volatility target / sqrt(256)
        :return:                                dict of tuples(price volatility, volatility scalar) with market IDs as keys
        """
        volatility = {}
        for market in [p.market() for p in self.__positions]:
            point_value = market.point_value()
            block_value = prices[market.id()] * point_value
            price_volatility = correlation_data[market.id()][Table.MarketCorrelation.VOLATILITY]
            instrument_currency_volatility = price_volatility * block_value
            instrument_value_volatility = self.__account.base_value(instrument_currency_volatility, market.currency(), date)
            volatility_scalar = daily_cash_volatility_target / instrument_value_volatility
            volatility[market.id()] = price_volatility, volatility_scalar

        return volatility

    def __diversification_multiplier(self, volatility, correlations, market_weights):
        print volatility, correlations, market_weights
        terms = []
        for pair in correlations.keys():
            market_1_vol = volatility[int(pair[0])][0] * 16
            market_2_vol = volatility[int(pair[1])][0] * 16
            market_1_weight = market_weights[pair[0]]
            market_2_weight = market_weights[pair[1]]
            correlation = correlations[pair] if correlations[pair] >= 0.0 else 0.0
            terms.append(market_1_weight**2 * market_1_vol**2)
            terms.append(market_2_weight**2 * market_2_vol**2)
            terms.append(2 * market_1_weight * market_1_vol * market_2_weight * market_2_vol * correlation)

            # print 'DM: ', pair, market_1_vol, market_2_vol, market_1_weight, market_2_weight, correlation

        portfolio_volatility = sqrt(abs(sum(terms))) if len(terms) else self.__volatility_target
        print portfolio_volatility, self.__volatility_target / portfolio_volatility

        return self.__volatility_target / portfolio_volatility
