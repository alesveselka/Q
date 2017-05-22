#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal
from abc import ABCMeta, abstractmethod


class TradingModel:
    """
    Abstract Base Class for all trading models
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        raise NotImplementedError("Should implement 'signals()'")


class BreakoutMAFilterATRStop(TradingModel):
    """
    Breakout Trend-Following model.
    
    Signal is generated when price breaks highest high or lowest low in specified period, 
    but only in the direction of a trend defined by MA crossover.
    Exit stops are at ATR multiples.
    """

    def __init__(self, markets, params):
        self.__markets = markets
        self.__params = params

    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        signals = []

        for market in self.__markets:

            if date > market.first_study_date() and market.has_data(date):
                market_data = market.data(end_date=date)
                previous_date = market_data[-2][Table.Market.PRICE_DATE]
                ma_long = market.study(Study.MA_LONG, date)[-1][Table.Study.VALUE]
                ma_short = market.study(Study.MA_SHORT, date)[-1][Table.Study.VALUE]
                hhll_short = market.study(Study.HHLL_SHORT, previous_date)[-1]
                settle_price = market_data[-1][Table.Market.SETTLE_PRICE]
                market_position = self.__market_position(positions, market)

                # TODO pass in rules
                if market_position:
                    direction = market_position.direction()
                    if direction == Direction.LONG:
                        if settle_price <= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, Direction.SHORT, date, settle_price))
                    elif direction == Direction.SHORT:
                        if settle_price >= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, Direction.LONG, date, settle_price))

                    # TODO REBALANCE (during rolls?)!
                    # Naive contract roll implementation (end of each month)
                    if date.month != previous_date.month and len([s for s in signals if s.market() == market]) == 0:
                        opposite_direction = Direction.LONG if direction == Direction.SHORT else Direction.LONG
                        signals.append(Signal(market, SignalType.ROLL_EXIT, opposite_direction, date, settle_price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, settle_price))

                # TODO pass-in rules
                if ma_short > ma_long:
                    if settle_price > hhll_short[Table.Study.VALUE]:
                        signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, settle_price))

                elif ma_short < ma_long:
                    if settle_price < hhll_short[Table.Study.VALUE_2]:
                        signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, settle_price))

        return signals

    def __stop_loss(self, date, position):
        """
        Calculate and return Stop Loss price for the position and date passed in
        
        :param date:        date on when to calculate the stop loss
        :param position:    position for which to calculate the stop loss
        :return:            Decimal price representing the stop loss
        """
        market = position.market()
        position_data = market.data(position.enter_date(), date)
        prices = [d[Table.Market.SETTLE_PRICE] for d in position_data]
        atr = market.study(Study.ATR_SHORT, date)[-1][Table.Study.VALUE]
        # TODO hard-coded values
        risk = 3 * atr
        return max(prices) - risk if position.direction() == Direction.LONG else min(prices) + risk

    def __market_position(self, positions, market):
        """
        Find and return position by market passed in
        
        :param positions:   list of open positions
        :param market:      Market to filter by
        :return:            Position object
        """
        positions = [p for p in positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None
