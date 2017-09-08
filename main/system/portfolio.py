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
        correlations, market_weights = self.__correlation_weights(date)
        volatility = self.__volatility_scalars(date, daily_cash_volatility_target)

        # volatility = {1: (0.00625, 10), 2: (0.00625, 10)}
        # correlations = {('1', '2'): -0.6}
        # market_weights = {'1': 0.5, '2': 0.5}
        if len(volatility):
            dm = self.__diversification_multiplier(date, volatility, correlations, market_weights)
            for market_id in volatility.keys():
                w = market_weights[str(market_id)] if len(market_weights) else 1.0
                print \
                    market_id, \
                    volatility[market_id][1], \
                    w, \
                    dm, \
                    round(volatility[market_id][1] * w * dm, 2)  # final position!

    def __correlation_weights(self, date):
        # TODO The 'Handcrafting' method assumes the assets have the same expected standard deviation of returns!
        # TODO also incorporate new orders and create DIFF
        markets = [p.market() for p in self.__positions]
        correlations = {}
        market_weights = {}
        if len(markets) >= 2:
            market_ids = {str(m.id()): m for m in markets}
            pairs = list(combinations(market_ids.keys(), 2))
            groups = defaultdict(list)
            market_correlations = defaultdict(list)
            group_correlations = defaultdict(list)
            fraction = .25
            # print date, market_ids.keys(), pairs
            for pair in pairs:
                # TODO receive date as in vol. scalars
                correlation_data = market_ids[pair[0]].correlation(date)
                volatility = correlation_data[Table.MarketCorrelation.VOLATILITY]
                correlation = json.loads(correlation_data[Table.MarketCorrelation.CORRELATIONS])[pair[1]]
                correlation = 1e-6 if correlation == 0.0 else abs(correlation)
                # correlations[pair] = correlation
                correlations[pair] = 1e-6 if correlation == 0.0 else correlation
                market_correlations[pair[0]].append(correlation)
                market_correlations[pair[1]].append(correlation)
                rounded_correlation = (fraction * round(correlation/fraction)) if correlation else None
                group_correlations[pair[0]].append(rounded_correlation)
                group_correlations[pair[1]].append(rounded_correlation)
                groups[rounded_correlation].append({pair: round(correlation, 2)})
                print pair, round(correlation, 2), rounded_correlation, volatility, correlation

            # print date, market_correlations, group_correlations

            # TODO if there is only one group, no need to calculate average AND not need to use group at first place
            group_weights = {}
            if len(group_correlations) > 1:
                logs = 0
                for k in group_correlations.keys():
                    avg = sum(group_correlations[k]) / len(group_correlations[k])
                    ln = (log(avg) if avg else log(1e-6))
                    ln = 1-1e-6 if avg == 1.0 else ln
                    logs += ln
                for k in group_correlations.keys():
                    avg = sum(group_correlations[k]) / len(group_correlations[k])
                    ln = (log(avg) if avg else log(1e-6))
                    ln = 1-1e-6 if avg == 1.0 else ln
                    group_weights[k] = ln / logs
                    # print k, group_correlations[k], round(avg, 2), round(ln, 2), round(ln / logs, 3)

            logs = 0
            grp_logs = 0
            for k in market_correlations.keys():
                logs += log(reduce(mul, market_correlations[k]))
                grp_logs += log(reduce(mul, market_correlations[k])**group_weights[k])
            for k in market_correlations.keys():
                product = reduce(mul, market_correlations[k])
                # market_weights[k] = log(product) / logs
                market_weights[k] = log(product**group_weights[k]) / grp_logs
                print \
                    k, \
                    market_correlations[k], \
                    round(product, 6), \
                    round(log(product), 2), \
                    round(log(product) / logs, 3), \
                    round(log(product**group_weights[k]) / grp_logs, 3)

        return correlations, market_weights

    def __volatility_scalars(self, date, daily_cash_volatility_target):
        markets = [p.market() for p in self.__positions]
        # scalars = {}
        volatility = {}
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
            # scalars[market.id()] = volatility_scalar
            volatility[market.id()] = price_volatility, volatility_scalar
            print \
                market.code(), \
                int(daily_cash_volatility_target), \
                price, \
                point_value, \
                block_value, \
                price_volatility, \
                instrument_currency_volatility, \
                instrument_value_volatility, \
                volatility_scalar

        return volatility

    def __diversification_multiplier(self, date, volatility, correlations, market_weights):
        print date, volatility, correlations, market_weights
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
        print date, terms, portfolio_volatility, self.__volatility_target / portfolio_volatility

        return self.__volatility_target / portfolio_volatility
