#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class BreakoutMAFilterATRStop(TradingModel):
    """
    Breakout Trend-Following model.
    
    Signal is generated when price breaks highest high or lowest low in specified period, 
    but only in the direction of a trend defined by MA crossover.
    Exit stops are at ATR multiples.
    """

    def __init__(self, markets, params):
        self.__markets = markets
        self.__stop_multiple = int(params['stop_multiple'])

    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        signals = []

        for market in self.__markets:
            market_data, previous_data = market.data(date)

            if market.has_study_data() and market_data:
                previous_date = previous_data[Table.Market.PRICE_DATE]
                ma_long = market.study(Study.MA_LONG, date)[Table.Study.VALUE]
                ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]
                hhll_short = market.study(Study.HHLL_SHORT, previous_date)
                settle_price = market_data[Table.Market.SETTLE_PRICE]
                market_position = self._market_position(positions, market)

                if market_position:
                    direction = market_position.direction()
                    if direction == Direction.LONG:
                        if settle_price <= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, settle_price))
                    elif direction == Direction.SHORT:
                        if settle_price >= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, settle_price))

                    if self._should_roll(date, previous_date, market, market_position.contract(), signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, settle_price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, settle_price))

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
        :return:            price representing the stop loss
        """
        prices = position.prices()
        atr = position.market().study(Study.ATR_SHORT, date)[Table.Study.VALUE]
        risk = atr * self.__stop_multiple
        return max(prices) - risk if position.direction() == Direction.LONG else min(prices) + risk
