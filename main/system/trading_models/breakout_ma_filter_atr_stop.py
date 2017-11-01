#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel
from trading_models.binary_trading_model import BinaryTradingModel


class BreakoutMAFilterATRStop(TradingModel, BinaryTradingModel):
    """
    Breakout Trend-Following model.
    
    Signal is generated when price breaks highest high or lowest low in specified period, 
    but only in the direction of a trend defined by MA crossover.
    Exit stops are at ATR multiples.
    """

    def __init__(self, name, markets, params):
        TradingModel.__init__(self, name)
        BinaryTradingModel.__init__(self, params['rebalance_interval'], params['roll_lookout_days'])

        self.__markets = markets
        self.__stop_multiple = int(params['stop_multiple'])
        self.__forecast = 10.0
        self.__positions_enter_dates = {}

    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        signals = []

        self.__update_enter_dates(date, positions)

        for market in self.__markets:
            market_data, previous_data = market.data(date)

            if market.has_study_data() and market_data:
                market_id = str(market.id())
                market_positions = {k.split('_')[1]: positions[k] for k in positions.keys() if k.split('_')[0] == market_id}
                market_position = market_positions.items()[0] if len(market_positions) else None
                previous_date = previous_data[Table.Market.PRICE_DATE]
                settle_price = market_data[Table.Market.SETTLE_PRICE]

                if market_position:
                    position_contract = market_position[0]
                    position_quantity = market_position[1]
                    direction = Direction.LONG if position_quantity > 0 else Direction.SHORT
                    # Exit
                    if direction == Direction.LONG:
                        if settle_price <= self.__stop_loss(date, market, market_id, direction):
                            signals.append(Signal(date, market, position_contract, 0, settle_price))
                    elif direction == Direction.SHORT:
                        if settle_price >= self.__stop_loss(date, market, market_id, direction):
                            signals.append(Signal(date, market, position_contract, 0, settle_price))
                    # Roll
                    if self._should_roll(date, previous_date, market, position_contract, signals):
                        sign = 1 if position_quantity > 0 else -1
                        signals.append(Signal(date, market, position_contract, 0, settle_price))
                        signals.append(Signal(date, market, market.contract(date), self.__forecast * sign, settle_price))
                    # Rebalance
                    if self._should_rebalance(market, position_contract, date, previous_date, signals):
                        sign = 1 if position_quantity > 0 else -1
                        signals.append(Signal(date, market, position_contract, self.__forecast * sign, settle_price))
                else:
                    ma_long = market.study(Study.MA_LONG, date)[Table.Study.VALUE]
                    ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]
                    hhll_short = market.study(Study.HHLL_SHORT, previous_date)
                    contract = market.contract(date)
                    # Enter
                    if ma_short > ma_long:
                        if settle_price > hhll_short[Table.Study.VALUE]:
                            signals.append(Signal(date, market, contract, self.__forecast, settle_price))

                    elif ma_short < ma_long:
                        if settle_price < hhll_short[Table.Study.VALUE_2]:
                            signals.append(Signal(date, market, contract, -self.__forecast, settle_price))

        return signals

    def __stop_loss(self, date, market, market_id, direction):
        """
        Calculate and return Stop Loss price for the position and date passed in
        
        :param date:        date on when to calculate the stop loss
        :param position:    position for which to calculate the stop loss
        :return:            price representing the stop loss
        """
        data = market.data_range(self.__positions_enter_dates[market_id], date)
        prices = [d[Table.Market.SETTLE_PRICE] for d in data]
        atr = market.study(Study.ATR_SHORT, date)[Table.Study.VALUE]
        risk = atr * self.__stop_multiple
        return max(prices) - risk if direction == Direction.LONG else min(prices) + risk

    def __update_enter_dates(self, date, positions):
        """
        Update dict with market IDs and their respective position enter dates
        
        :param date:        current date
        :param positions:   dict of positions(market_id_market_contract: quantity)
        """
        position_ids = [k.split('_')[0] for k in positions.keys()]
        for market_id in position_ids:
            if market_id not in self.__positions_enter_dates:
                self.__positions_enter_dates[market_id] = date

        for key in self.__positions_enter_dates.keys():
            if key not in position_ids:
                self.__positions_enter_dates.pop(key, None)
