#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class MATrendOnPullback(TradingModel):
    """
    MA Trend model.
    
    Signal is generated when price pulls back beyond shorter MA and then turns back.
    Signal is in direction of a trend defined by two MAs and pullback is against the actual trend.
    Exit stops are at ATR multiples.
    """

    def __init__(self, markets, params, roll_strategy):
        self.__markets = markets
        self.__stop_multiple = int(params['stop_multiple'])
        self.__roll_strategy = roll_strategy

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
                price = market_data[Table.Market.SETTLE_PRICE]
                market_position = self.__market_position(positions, market)
                previous_price = previous_data[Table.Market.SETTLE_PRICE]
                previous_ma_short = market.study(Study.MA_SHORT, previous_date)[Table.Study.VALUE]

                if market_position:
                    direction = market_position.direction()
                    if direction == Direction.LONG:
                        if price <= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, price))
                    elif direction == Direction.SHORT:
                        if price >= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, price))

                    if self.__should_roll(date, previous_date, market, market_position.contract(), signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, price))

                if ma_short > ma_long:
                    if previous_price < previous_ma_short and price > ma_short:
                        signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, price))

                elif ma_short < ma_long:
                    if previous_price > previous_ma_short and price < ma_short:
                        signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, price))

        return signals

    def __should_roll(self, date, previous_date, market, position_contract, signals):
        """
        Check if position should roll to the next contract
        
        :param date:                current date
        :param previous_date:       previous date
        :param market:              market of the position
        :param position_contract:   position contract
        :param signals:             signals
        :return:                    Boolean indicating if roll signals should be generated
        """
        should_roll = False

        if len([s for s in signals if s.market() == market]) == 0:
            contract = market.contract(date)
            should_roll = (contract != position_contract and contract != market.contract(previous_date)) \
                if position_contract else date.month != previous_date.month

        return should_roll

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

    def __market_position(self, positions, market):
        """
        Find and return position by market passed in
        
        :param positions:   list of open positions
        :param market:      Market to filter by
        :return:            Position object
        """
        positions = [p for p in positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None