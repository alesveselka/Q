#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import StopType
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class PlungeATRStopProfit(TradingModel):
    """
    'Plunge' model.
    
    Signal is generated in direction of trend, but only when price recedes from extreme.
    Exit stops and Profit targets are at ATR multiples.
    """

    def __init__(self, markets, params):
        self.__markets = markets
        self.__enter_multiple = int(params['enter_multiple'])
        self.__stop_multiple = int(params['stop_multiple'])
        self.__profit_multiple = int(params['profit_multiple'])
        self.__stop_type = params['stop_type']
        self.__stop_time = int(params['stop_time'])
        self.__forecast = 10.0  # TODO load from params
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
                ma_long = market.study(Study.MA_LONG, date)[Table.Study.VALUE]
                ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]
                settle_price = market_data[Table.Market.SETTLE_PRICE]
                trend_direction = Direction.LONG if ma_short > ma_long else Direction.SHORT

                if market_position:
                    position_contract = market_position[0]
                    position_quantity = market_position[1]
                    direction = Direction.LONG if position_quantity > 0 else Direction.SHORT
                    if direction == trend_direction:
                        previous_date = previous_data[Table.Market.PRICE_DATE]
                        if self.__should_exit(date, market, market_id, settle_price, direction):
                            # Exit
                            signals.append(Signal(date, market, position_contract, 0, settle_price))

                        if self._should_roll(date, previous_date, market, position_contract, signals):
                            # Roll
                            sign = 1 if position_quantity > 0 else -1
                            signals.append(Signal(date, market, position_contract, 0, settle_price))
                            signals.append(Signal(date, market, market.contract(date), self.__forecast * sign, settle_price))
                    else:
                        # Exit in case of trend change
                        signals.append(Signal(date, market, position_contract, 0, settle_price))
                else:
                    if self.__plunge(date, market, settle_price, trend_direction) > self.__enter_multiple:
                        # Enter
                        contract = market.contract(date)
                        signals.append(Signal(date, market, contract, self.__forecast, settle_price))

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

    def __should_exit(self, date, market, market_id, price, direction):
        """
        Return boolean flag indicating if position should be exited based on params passed in and type of stop loss
        
        :param date:        date of data
        :param market:      market for which to check exit
        :param market_id:   ID of the market
        :param price:       current Settle price
        :param direction:   direction of the position
        :return:            boolean flag
        """
        should_exit = False
        short = direction == Direction.SHORT

        if self.__stop_type == StopType.TRAILING_STOP:
            should_exit = price >= self.__stop_loss(date, market, market_id, direction) if short else \
                          price <= self.__stop_loss(date, market, market_id, direction)
        elif self.__stop_type == StopType.FIXED_STOP:
            should_exit = price >= self.__stop_loss(date, market, market_id, direction) or \
                          price <= self.__profit_target(date, market, market_id, direction) if short else \
                          price <= self.__stop_loss(date, market, market_id, direction) or \
                          price >= self.__profit_target(date, market, market_id, direction)
        elif self.__stop_type == StopType.TIME:
            should_exit = (date - self.__positions_enter_dates[market_id]).days >= self.__stop_time

        return should_exit

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
        stop_price = 0.0

        if self.__stop_type == StopType.TRAILING_STOP:
            stop_price = max(prices) - risk if direction == Direction.LONG else min(prices) + risk
        elif self.__stop_type == StopType.FIXED_STOP:
            enter_price = prices[0]
            stop_price = enter_price - risk if direction == Direction.LONG else enter_price + risk

        return stop_price

    def __profit_target(self, date, market, market_id, direction):
        """
        Calculate and return Profit Target price for the position and date passed in
        
        :param date:        date on when to calculate the profit target
        :param position:    position for which to calculate the profit target
        :return:            price representing the profit target
        """
        data = market.data_range(self.__positions_enter_dates[market_id], date)
        enter_price = data[0][Table.Market.SETTLE_PRICE]
        atr = market.study(Study.ATR_SHORT, date)[Table.Study.VALUE]
        profit = atr * self.__profit_multiple
        return enter_price + profit if direction == Direction.LONG else enter_price - profit

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
