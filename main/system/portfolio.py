#!/usr/bin/python

import json
import datetime as dt
from math import log
from math import sqrt
from operator import mul
from operator import itemgetter
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

            self.__calculate_positions(price_date, prices, correlation_data, daily_cash_volatility_target)

    def __calculate_positions(self, price_date, prices, correlation_data, daily_cash_volatility_target):
        correlations, market_weights = self.__correlation_weights(correlation_data)
        volatility = self.__volatility_scalars(price_date, prices, correlation_data, daily_cash_volatility_target)

        # correlations, market_weights = self.__correlation_weights({
        #     'SP': (dt.date(1992, 5, 31), 0.03, '{"NQ": 0.8, "US": -0.3}'),
        #     'NQ': (dt.date(1992, 5, 31), 0.03, '{"SP": 0.8, "US": -0.3}'),
        #     'US': (dt.date(1992, 5, 31), 0.005, '{"SP": -0.3, "NQ": -0.3}')
        # })
        # volatility = {'SP': (0.00625, 10), 'NQ': (0.00625, 10), 'US': (0.00625, 10)}

        diversification_multiplier = self.__volatility_target / self.__optimal_volatility(volatility, correlations, market_weights)
        position_sizes = {k: volatility[k][1] * (market_weights[k] if len(market_weights) else 1.0) * diversification_multiplier for k in volatility.keys()}
        fractional_sizes = filter(lambda k: position_sizes[k] < 1, position_sizes.keys())
        print 'position_sizes', position_sizes
        # print 'fractional_sizes', fractional_sizes
        print 'sorted by weight', sorted(market_weights, key=market_weights.get)

        for market_id in volatility.keys():
            w = market_weights[market_id] if len(market_weights) else 1.0
            print \
                market_id, \
                volatility[market_id][1], \
                w, \
                diversification_multiplier, \
                round(volatility[market_id][1] * w * diversification_multiplier, 2)  # final position!

        print '-' * 50

        market_ids = sorted(market_weights, key=market_weights.get)[1:]
        # TODO mark as 'Rejected'
        if len(fractional_sizes) and len(market_ids):
            correlation_data = {m: correlation_data[m] for m in market_ids}
            prices = {m: prices[m] for m in market_ids}

            self.__calculate_positions(price_date, prices, correlation_data, daily_cash_volatility_target)

    def __correlation_weights(self, correlation_data, use_group_correlations=False):
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
                correlation = json.loads(correlation_data[pair_1_id][Table.MarketCorrelation.CORRELATIONS])[str(pair_2_id)] \
                    if correlation_data[pair_1_id] else 0.3
                correlations[pair] = correlation
                correlation = 1e-3 if correlation == 0.0 else abs(correlation)
                market_correlations[pair_1_id].append(correlation)
                market_correlations[pair_2_id].append(correlation)
                rounded_correlation = (fraction * round(correlation / fraction)) if correlation else None
                group_correlations[pair_1_id].append(rounded_correlation)
                group_correlations[pair_2_id].append(rounded_correlation)

            market_weights = self.__grouped_market_weights(market_correlations, group_correlations) \
                if use_group_correlations else self.__market_weights(market_correlations)

            print 'correlations and weights'
            for m in market_weights.keys():
                print m, [round(c, 3) for c in market_correlations[m]], market_weights[m]

        return correlations, market_weights

    def __market_weights(self, market_correlations):
        """
        Calculate market weights based on inter-market correlations
        
        :param market_correlations:     dict{market ID: list of correlations with every other market}
        :return:                        dict of market position weights
        """
        market_ids = market_correlations.keys()
        market_weights = {m: reduce(mul, market_correlations[m]) for m in market_ids}
        logs = sum(log(market_weights[m]) for m in market_ids)
        return {m: log(market_weights[m]) / logs for m in market_ids}

    def __grouped_market_weights(self, market_correlations, group_correlations):
        """
        Calculate market weights based on inter-market correlations and also 'grouped' inter-correlations
        
        :param market_correlations:     dict{market ID: list of correlations with every other market}
        :return:                        dict of market position weights
        """
        market_ids = market_correlations.keys()
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
        return {m: log(market_weights[m]**group_weights[m]) / group_logs for m in market_ids}

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
        market_ids = correlation_data.keys()
        print 'volatility'
        for market in [p.market() for p in self.__positions if p.market().id() in market_ids]:
            market_id = market.id()
            point_value = market.point_value()
            block_value = prices[market_id] * point_value
            price_volatility = correlation_data[market_id][Table.MarketCorrelation.VOLATILITY] if correlation_data[market_id] else 0.02
            instrument_currency_volatility = price_volatility * block_value
            instrument_value_volatility = self.__account.base_value(instrument_currency_volatility, market.currency(), date)
            volatility_scalar = daily_cash_volatility_target / instrument_value_volatility
            volatility[market_id] = price_volatility, volatility_scalar

            print market_id, instrument_value_volatility, volatility_scalar

        return volatility

    def __optimal_volatility(self, volatility, correlations, market_weights):
        """
        Calculate diversification multiplier based on markets volatility and correlations
        
        :param volatility:      dict of markets volatility
        :param correlations:    dict of markets correlations
        :param market_weights:  dict of market weights
        :return:                return diversification multiplier based on portfolio volatility and volatility target
        """
        terms = []
        for pair in correlations.keys():
            pair_1_id = pair[0]
            pair_2_id = pair[1]
            market_1_vol = volatility[pair_1_id][0] * 16
            market_2_vol = volatility[pair_2_id][0] * 16
            market_1_weight = market_weights[pair_1_id]
            market_2_weight = market_weights[pair_2_id]
            correlation = correlations[pair] if correlations[pair] >= 0.0 else 0.0  # Cap to avoid very big numbers
            terms.append(market_1_weight**2 * market_1_vol**2)
            terms.append(market_2_weight**2 * market_2_vol**2)
            terms.append(2 * market_1_weight * market_1_vol * market_2_weight * market_2_vol * correlation)

        return sqrt(abs(sum(terms))) if len(terms) else self.__volatility_target
