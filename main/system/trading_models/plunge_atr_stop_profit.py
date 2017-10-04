#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class PlungeATRStopProfit(TradingModel):
    """
    'Plunge' model.
    
    Signal is generated in direction of trend, but only when price recedes from extreme.
    Exit stops and Profit targets are at ATR multiples.
    """

    def __init__(self, markets, params, roll_strategy):
        self.__markets = markets
        self.__stop_multiple = int(params['stop_multiple'])
        self.__profit_multiple = int(params['profit_multiple'])
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
                settle_price = market_data[Table.Market.SETTLE_PRICE]
                market_position = self.__market_position(positions, market)

                if market_position:
                    direction = market_position.direction()
                    if direction == Direction.LONG:
                        if settle_price <= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, settle_price))
                    elif direction == Direction.SHORT:
                        if settle_price >= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, settle_price))

                    if self.__should_roll(date, previous_date, market, market_position.contract(), signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, settle_price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, settle_price))

                if ma_short > ma_long:
                    if settle_price > hhll_short[Table.Study.VALUE]:
                        signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, settle_price))

                elif ma_short < ma_long:
                    if settle_price < hhll_short[Table.Study.VALUE_2]:
                        signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, settle_price))

        return signals

    def __plunge(self, date, market, price, direction):
        """
        Calculate value of 'Plunger' indicator:
            1. Check overall direction -- this is passed in
            2. Check 20-day ATR
            3. Check 20-day extreme price (highest-high or lowest-low)
            4. Divide distance of current price from extreme by ATR. Absolute value is 'Plunger'
        
        :param date:        date of calculation
        :param market:      market for which to calculate the indicator
        :param price:       Settle price of the date passed in
        :param direction:   direction of price trend
        :return:            Number representing Plunger value
        """
        # TODO 'Plunger' uses High and Low for extremes, 'HHLL' calculates from Settle
        hhll = market.study(Study.HHLL_SHORT, date)
        diff = abs(price - hhll[Table.Study.VALUE]) if direction == Direction.LONG else abs(price - hhll[Table.Study.VALUE_2])
        atr = market.study(Study.ATR_SHORT, date)[Table.Study.VALUE]
        return diff / atr

    # TODO refactor and inherit?
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

    # TODO refactor and inherit?
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

    def __profit_target(self, date, position):
        """
        Calculate and return Profit Target price for the position and date passed in
        
        :param date:        date on when to calculate the profit target
        :param position:    position for which to calculate the profit target
        :return:            price representing the profit target
        """
        prices = position.prices()
        atr = position.market().study(Study.ATR_SHORT, date)[Table.Study.VALUE]
        profit = atr * self.__profit_multiple
        # TODO ATRx from Entry price
        return max(prices) - profit if position.direction() == Direction.LONG else min(prices) + profit

    # TODO refactor and inherit?
    def __market_position(self, positions, market):
        """
        Find and return position by market passed in
        
        :param positions:   list of open positions
        :param market:      Market to filter by
        :return:            Position object
        """
        positions = [p for p in positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None
