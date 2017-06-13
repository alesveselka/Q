#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from enum import YieldCurve
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class BreakoutMAFilterATRStop(TradingModel):
    """
    Breakout Trend-Following model.
    
    Signal is generated when price breaks highest high or lowest low in specified period, 
    but only in the direction of a trend defined by MA crossover.
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

            if date > market.first_study_date() and market.has_data(date):
                market_data = market.data(end_date=date)
                previous_date = market_data[-2][Table.Market.PRICE_DATE]
                ma_long = market.study(Study.MA_LONG, date)[-1][Table.Study.VALUE]
                ma_short = market.study(Study.MA_SHORT, date)[-1][Table.Study.VALUE]
                hhll_short = market.study(Study.HHLL_SHORT, previous_date)[-1]
                settle_price = market_data[-1][Table.Market.SETTLE_PRICE]
                market_position = self.__market_position(positions, market)

                if market_position:
                    direction = market_position.direction()
                    position_contract = market_position.contract()
                    if direction == Direction.LONG:
                        if settle_price <= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, settle_price, position_contract))
                    elif direction == Direction.SHORT:
                        if settle_price >= self.__stop_loss(date, market_position):
                            signals.append(Signal(market, SignalType.EXIT, direction, date, settle_price, position_contract))

                    if self.__should_roll(date, previous_date, market, market_position, signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, settle_price, position_contract))
                        contract = self.__roll_in_contract(market, position_contract)
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, settle_price, contract))

                if ma_short > ma_long:
                    if settle_price > hhll_short[Table.Study.VALUE]:
                        contract = self.__contract(date, market, Direction.LONG)
                        signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, settle_price, contract))

                elif ma_short < ma_long:
                    if settle_price < hhll_short[Table.Study.VALUE_2]:
                        contract = self.__contract(date, market, Direction.SHORT)
                        signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, settle_price, contract))

        return signals

    def __contract(self, date, market, direction):
        """
        Find 'optimal' contract to trade
        
        :param date:        date of the signal
        :param market:      market to trade
        :param direction:   direction of trade signal
        :return:            string representing code of contract to trade
        """
        min_volume = 1000
        yield_curve = market.yield_curve(date)
        current = [y for y in yield_curve if y[YieldCurve.YIELD] is None][0]
        candidates = [y for y in yield_curve if y[YieldCurve.YIELD] is not None and y[YieldCurve.VOLUME] >= min_volume]
        optimal = current

        if len(candidates):
            fn = max if direction == Direction.SHORT else min
            best = fn([c[YieldCurve.YIELD] for c in candidates])
            optimal = [c for c in candidates if c[YieldCurve.YIELD] == best][0]

        return {'optimal_roll': optimal, 'standard_roll': current}.get(self.__roll_strategy[Table.RollStrategy.TYPE])[0]

    def __roll_in_contract(self, market, contract):
        """
        Find and retun roll-in contract
        
        :param market:      contract's market
        :param contract:    current 'roll out' contract
        :return:            contract to roll in
        """
        return market.contract_roll(contract)[Table.ContractRoll.ROLL_IN_CONTRACT]

    def __should_roll(self, date, previous_date, market, position, signals):
        """
        Check if position should roll to the next contract
        
        :param date:            current date
        :param previous_date:   previous date
        :param market:          market of the position
        :param position:        position to roll
        :param signals:         signals
        :return:                Boolean indicating if roll signals should be generated
        """
        should_roll = False

        if len([s for s in signals if s.market() == market]) == 0:
            position_contract = position.contract()
            if position_contract is None:
                should_roll = date.month != previous_date.month
            else:
                contract_roll = market.contract_roll(position_contract)
                roll_date = market.data(end_date=contract_roll[Table.ContractRoll.DATE])[-2][Table.Market.PRICE_DATE]
                should_roll = date == roll_date and position_contract == contract_roll[Table.ContractRoll.ROLL_OUT_CONTRACT]

        return should_roll

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
