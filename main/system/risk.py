#!/usr/bin/python

import json
from math import log
from math import sqrt
from operator import mul
from itertools import combinations
from collections import defaultdict
from enum import Study
from enum import Table
from enum import PositionSizing
from enum import CapitalCorrection
from decimal import Decimal


class Risk(object):

    def __init__(self,
                 account,
                 position_sizing,
                 risk_factor,
                 volatility_target,
                 use_group_correlation_weights,
                 capital_correction,
                 partial_compounding_factor,
                 forecast_const):
        self.__account = account
        self.__position_sizing = position_sizing
        self.__risk_factor = risk_factor
        self.__volatility_target = volatility_target
        self.__use_group_correlation_weights = use_group_correlation_weights
        self.__capital_correction = capital_correction
        self.__partial_compounding_factor = partial_compounding_factor
        self.__use_correlation_weights = False
        self.__forecast_const = forecast_const

    def position_sizes(self, date, markets, forecasts):
        """
        Calculate position sized based on position sizing type and params
        
        :param date date:           date of data
        :param list markets:        markets to calculate position sizes for
        :param dict forecasts:      signal forecast of each market
        :return dict(int: float):   dict of position sizes as values and market IDs as keys
        """
        daily_factor = 16  # sqrt(256 business days)
        cash_volatility_target = self.__risk_capital(date) * self.__volatility_target
        daily_cash_volatility_target = cash_volatility_target / daily_factor
        position_sizes = {}

        if len(markets):
            price_date = date
            prices = {}
            correlation_data = {}
            for market in markets:
                market_data, _ = market.data(date)
                data = market_data if market_data else market.data_range(end_date=date)[-1]
                price_date = data[Table.Market.PRICE_DATE]
                prices[market.id()] = data[Table.Market.SETTLE_PRICE]
                correlation_data[market.id()] = market.correlation(price_date)
            # TODO filter too expensive positions
            position_sizes = {
                PositionSizing.RISK_FACTOR: self.__fixed_risk_sizes,
                PositionSizing.EQUAL_WEIGHTS: self.__equally_weighted_sizes,
                PositionSizing.CORRELATION_WEIGHTS: self.__correlation_weighted_sizes
            }[self.__position_sizing](
                price_date,
                prices,
                correlation_data,
                daily_cash_volatility_target,
                markets,
                forecasts
            )

        return {k: int(position_sizes[k]) for k in position_sizes.keys() if abs(position_sizes[k]) >= 1.0}

    def __fixed_risk_sizes(self, date, prices, correlation_data, vol_target, markets, forecasts):
        """
        Calculate position sizes based on recent volatility
        
        :param date:                date of the data
        :param prices:              dict of prices and market IDs as keys
        :param correlation_data:    correlation data among individual markets
        :param vol_target:          daily cash volatility target
        :param markets:             list of markets to use in calculation
        :param dict forecasts:      signal forecast of each market
        :return:                    dict of position sizes and market IDs as keys
        """
        position_sizes = {}
        risk = self.__risk_capital(date) * self.__risk_factor
        for market in markets:
            base_point_value = float(self.__account.base_value(market.point_value(), market.currency(), date))
            atr_study = market.study(Study.ATR_LONG, date)
            vol_study = market.study(Study.VOL_SHORT, date)
            atr = atr_study[Table.Study.VALUE] if atr_study else market.study_range(Study.ATR_LONG, end_date=date)[-1][Table.Study.VALUE]
            vol = vol_study[Table.Study.VALUE] if vol_study else market.study_range(Study.VOL_SHORT, end_date=date)[-1][Table.Study.VALUE]
            position_size = risk / (atr * base_point_value)
            if position_size < vol:
                position_sizes[market.id()] = position_size

        # Make sure correlation data is loaded
        if self.__use_correlation_weights:
            l = len(position_sizes)
            correlations, market_weights = self.__correlation_weights(correlation_data, markets)
            position_sizes = {k: position_sizes[k] * l * market_weights[k] for k in position_sizes.keys()}

        fractional_sizes = filter(lambda market_id: position_sizes[market_id] < 1, position_sizes.keys())
        updated_markets = [m for m in markets if m.id() not in fractional_sizes]

        return self.__fixed_risk_sizes(date, prices, correlation_data, vol_target, updated_markets, forecasts) \
            if len(fractional_sizes) and len(updated_markets) else position_sizes

    def __equally_weighted_sizes(self, date, prices, correlation_data, vol_target, markets, forecasts):
        """
        Calculate position sizes for the markets passed in based on volatility data
        
        :param date:                date of the data
        :param prices:              dict of prices and market IDs as keys
        :param correlation_data:    correlation data among individual markets
        :param vol_target:          daily cash volatility target
        :param markets:             list of markets to use in calculation
        :param dict forecasts:      signal forecast of each market
        :return:                    dict of position sizes and market IDs as keys
        """
        market_ids = [m.id() for m in markets]
        volatility, volatility_scalars = self.__volatility_scalars(date, prices, correlation_data, vol_target, markets)
        weight = 1.0 / len(volatility)
        position_sizes = {}
        for market_id in market_ids:
            forecast = forecasts[market_id] if market_id in forecasts else self.__forecast_const
            position_sizes[market_id] = (volatility_scalars[market_id] * forecast / self.__forecast_const) * weight
        illiquid_markets = self.__illiquid_markets(date, markets, position_sizes)
        liquid_position_sizes = {m: position_sizes[m] for m in market_ids if m not in illiquid_markets}
        fractional_sizes = filter(lambda m_id: abs(liquid_position_sizes[m_id]) < 1, liquid_position_sizes.keys())

        # TODO mark as 'Rejected'
        # TODO use volatility scalar as filter?
        # Sort by volatility and remove the one with lowest price volatility
        updated_market_ids = liquid_position_sizes.keys() if len(illiquid_markets) \
            else sorted(volatility, key=volatility.get)[1:]

        return self.__equally_weighted_sizes(
            date,
            prices,
            correlation_data,
            vol_target,
            [m for m in markets if m.id() in updated_market_ids],
            forecasts
        ) if (len(fractional_sizes) or len(illiquid_markets)) and len(updated_market_ids) else position_sizes

    def __correlation_weighted_sizes(self, date, prices, correlation_data, vol_target, markets, forecasts):
        """
        Calculate position sizes for the markets passed in based on correlation and volatility data
        
        :param date:                date of the data
        :param prices:              dict of prices and market IDs as keys
        :param correlation_data:    correlation data among individual markets
        :param vol_target:          daily cash volatility target
        :param markets:             list of markets to use in calculation
        :param dict forecasts:      signal forecast of each market
        :return:                    dict of position sizes and market IDs as keys
        """
        market_ids = [m.id() for m in markets]
        correlations, market_weights = self.__correlation_weights(correlation_data, markets)
        volatility, volatility_scalars = self.__volatility_scalars(date, prices, correlation_data, vol_target, markets)
        # Diversification multiplier
        DM = self.__volatility_target / self.__optimal_volatility(volatility, correlations, market_weights)
        position_sizes = {}
        for market_id in market_ids:
            weight = market_weights[market_id] if len(market_weights) else 1.0
            forecast = forecasts[market_id] if market_id in forecasts else self.__forecast_const
            position_sizes[market_id] = (volatility_scalars[market_id] * forecast / self.__forecast_const) * weight * DM
        illiquid_markets = self.__illiquid_markets(date, markets, position_sizes)
        liquid_position_sizes = {m: position_sizes[m] for m in market_ids if m not in illiquid_markets}
        fractional_sizes = filter(lambda market_id: abs(liquid_position_sizes[market_id]) < 1, liquid_position_sizes.keys())

        # TODO mark as 'Rejected'
        # Sort by correlation weights and remove the one with lowest weight
        updated_market_ids = liquid_position_sizes.keys() if len(illiquid_markets) \
            else sorted(market_weights, key=market_weights.get)[1:]

        return self.__correlation_weighted_sizes(
            date,
            prices,
            correlation_data,
            vol_target,
            [m for m in markets if m.id() in updated_market_ids],
            forecasts
        ) if (len(fractional_sizes) or len(illiquid_markets)) and len(updated_market_ids) else position_sizes

    def __correlation_weights(self, correlation_data, markets):
        """
        Calculate weights for each market based on correlations
        
        1. For each market, sum correlations with every other market;
        2. group market correlations and also sum these as 'group_weights';
        3. final weight for each market equals 'log(market correlations ^ group correlations) / sum of all correlations'
        
        :param correlation_data     correlation data of the markets
        :param markets              list of markets to use in calculation
        :return:                    tuple of
                                        dict of market correlations with market IDs as keys, and
                                        dict of correlation weights for each market with market IDs as keys
        """
        # TODO The 'Handcrafting' method assumes the assets have the same expected standard deviation of returns!
        correlations = {}
        market_weights = {}
        if len(markets) >= 2:
            market_ids = [m.id() for m in markets]
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

            market_weights = self.__grouped_market_weights(market_correlations, group_correlations, market_ids) \
                if self.__use_group_correlation_weights else self.__market_weights(market_correlations, market_ids)

        return correlations, market_weights

    def __market_weights(self, market_correlations, market_ids):
        """
        Calculate market weights based on inter-market correlations
        
        :param market_correlations:     dict{market ID: list of correlations with every other market}
        :param market_ids:              list of market IDs
        :return:                        dict of market position weights
        """
        inner_correlation = {market_id: reduce(mul, market_correlations[market_id]) for market_id in market_ids}
        logs = sum(log(inner_correlation[market_id]) for market_id in market_ids)
        return {market_id: log(inner_correlation[market_id]) / logs for market_id in market_ids}

    def __grouped_market_weights(self, market_correlations, group_correlations, market_ids):
        """
        Calculate market weights based on inter-market correlations and also 'grouped' inter-correlations
        
        :param market_correlations:     dict{market ID: list of correlations with every other market}
        :param market_ids:              list of market IDs
        :return:                        dict of market position weights
        """
        group_logs = {}
        for market_id in market_ids:
            avg = sum(group_correlations[market_id]) / len(group_correlations[market_id])
            ln = log(avg) if avg else log(1e-6)
            ln = 1-1e-6 if avg == 1.0 else ln
            group_logs[market_id] = ln

        total_group_logs = sum(group_logs[market_id] for market_id in market_ids)
        group_weights = {market_id: group_logs[market_id] / total_group_logs for market_id in market_ids}

        inner_correlation = {market_id: reduce(mul, market_correlations[market_id]) for market_id in market_ids}
        logs = sum(log(inner_correlation[market_id]**group_weights[market_id]) for market_id in market_ids)
        return {market_id: log(inner_correlation[market_id]**group_weights[market_id]) / logs for market_id in market_ids}

    def __volatility_scalars(self, date, prices, correlation_data, daily_cash_volatility_target, markets):
        """
        Calculate price volatility and volatility scalars for each market
        
        :param date:                            date on which to calculate
        :param prices:                          dict of prices and their respective market IDs as keys
        :param correlation_data:                dict of market ID as a key and record from 'market_correlation' as a value
        :param daily_cash_volatility_target:    equity x volatility target / sqrt(256)
        :param markets:                         list of markets to use in calculation
        :return:                                dict of tuples(price volatility, volatility scalar) with market IDs as keys
        """
        volatility = {}
        scalars = {}
        for market in markets:
            market_id = market.id()
            point_value = market.point_value()
            # TODO use actual contract prices -- continuous prices are distorted
            block_value = (abs(prices[market_id]) * point_value if abs(prices[market_id]) else point_value) / 100
            price_volatility = correlation_data[market_id][Table.MarketCorrelation.VOLATILITY] if correlation_data[market_id] else 0.02
            instrument_currency_volatility = price_volatility * block_value
            instrument_value_volatility = self.__account.base_value(instrument_currency_volatility, market.currency(), date)
            volatility_scalar = daily_cash_volatility_target / instrument_value_volatility
            volatility[market_id] = price_volatility
            scalars[market_id] = volatility_scalar

        return volatility, scalars

    def __optimal_volatility(self, volatility, correlations, market_weights):
        """
        Calculate diversification multiplier based on markets volatility and correlations
        
        :param volatility:      dict of markets volatility
        :param correlations:    dict of markets correlations
        :param market_weights:  dict of market weights
        :return:                return diversification multiplier based on portfolio volatility and volatility target
        """
        daily_factor = 16  # sqrt(256 business days)
        terms = []
        for pair in correlations.keys():
            pair_1_id = pair[0]
            pair_2_id = pair[1]
            market_1_vol = volatility[pair_1_id] * daily_factor
            market_2_vol = volatility[pair_2_id] * daily_factor
            market_1_weight = market_weights[pair_1_id]
            market_2_weight = market_weights[pair_2_id]
            correlation = correlations[pair] if correlations[pair] >= 0.0 else 0.0  # Cap to avoid very big numbers
            terms.append(market_1_weight**2 * market_1_vol**2)
            terms.append(market_2_weight**2 * market_2_vol**2)
            terms.append(2 * market_1_weight * market_1_vol * market_2_weight * market_2_vol * correlation)

        return sqrt(abs(sum(terms))) if len(terms) else self.__volatility_target

    def __illiquid_markets(self, date, markets, position_sizes):
        """
        Return list of markets for which there is not enough liquidity with given position sizes
        
        :param date date:           date of data
        :param list markets:        markets to check liquidity for
        :param dict position_sizes: position sizes for each market
        :return list(Market):       list of illiquid markets
        """
        illiquid_markets = []
        for market in markets:
            market_id = market.id()
            vol_study = market.study(Study.VOL_SHORT, date)
            vol = vol_study[Table.Study.VALUE] if vol_study \
                else market.study_range(Study.VOL_SHORT, end_date=date)[-1][Table.Study.VALUE]
            if abs(position_sizes[market_id]) > vol:
                illiquid_markets.append(market_id)

        return illiquid_markets

    def __risk_capital(self, date):
        """
        Return risk capital depending on 'capital correction' method
        
        :param date:    date of the capital
        :return:        number representing risk capital
        """
        equity = self.__account.equity(date)
        initial_balance = self.__account.initial_balance()
        partial_factor = Decimal(self.__partial_compounding_factor)
        capital = {
            CapitalCorrection.FIXED: initial_balance,
            CapitalCorrection.FULL_COMPOUNDING: equity,
            CapitalCorrection.HALF_COMPOUNDING: initial_balance if equity > initial_balance else equity,
            CapitalCorrection.PARTIAL_COMPOUNDING: (initial_balance + (equity - initial_balance) * partial_factor)
            if equity > initial_balance else equity
        }.get(self.__capital_correction, equity)
        return float(capital)
