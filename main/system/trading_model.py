#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal


class TradingModel:

    def __init__(self, markets, risk):
        self.__markets = markets
        self.__risk = risk

    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        # TODO pass in the configuration of parameters
        short_window = 50
        long_window = 100

        signals = []

        for market in self.__markets:
            market_data = market.data(end_date=date)

            # TODO replace hard-coded data
            if len(market_data) >= long_window + 1 and market.has_data(date):
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
                        if settle_price <= self.__risk.stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, Direction.SHORT, date, settle_price))
                    elif direction == Direction.SHORT:
                        if settle_price >= self.__risk.stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, Direction.LONG, date, settle_price))

                    # TODO REBALANCE (during rolls?)!
                    # Naive contract roll implementation (end of each month)
                    if date.month != previous_date.month and len([s for s in signals if s.market() == market]) == 0:
                        opposite_direction = Direction.LONG if direction == Direction.SHORT else Direction.LONG
                        signals.append(Signal(market, SignalType.ROLL_EXIT, opposite_direction, date, settle_price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, settle_price))

                # TODO pass-in rules
                # TODO use EMAs?
                if ma_short > ma_long:
                    if settle_price > hhll_short[Table.Study.VALUE]:
                        signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, settle_price))

                elif ma_short < ma_long:
                    if settle_price < hhll_short[Table.Study.VALUE_2]:
                        signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, settle_price))

        return signals

    def __market_position(self, positions, market):
        """
        Find and return position by market passed in
        
        :param positions:   list of open positions
        :param market:      Market to filter by
        :return:            Position object
        """
        positions = [p for p in positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None
