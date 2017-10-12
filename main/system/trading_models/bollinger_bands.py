#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class BollingerBands(TradingModel):
    """
    'Bollinger Bands' model.
    
    Signal is generated against direction of trend, when price(Close) returns from outside back inside of the bands.
    """

    def __init__(self, markets, params, roll_strategy):
        self.__markets = markets
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
                ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]
                atr = market.study(Study.ATR_SHORT, date)[Table.Study.VALUE]
                price = market_data[Table.Market.SETTLE_PRICE]
                position = self._market_position(positions, market)
                previous_date = previous_data[Table.Market.PRICE_DATE]
                previous_price = previous_data[Table.Market.SETTLE_PRICE]
                previous_ma_short = market.study(Study.MA_SHORT, previous_date)[Table.Study.VALUE]

                if position:
                    direction = position.direction()
                    if direction == Direction.LONG and previous_price < previous_ma_short and price >= ma_short:
                        signals.append(Signal(market, SignalType.EXIT, direction, date, price))
                    elif direction == Direction.SHORT and previous_price > previous_ma_short and price <= ma_short:
                        signals.append(Signal(market, SignalType.EXIT, direction, date, price))

                    # TODO temporal binding -- check if there are no positions ... (same with generating orders)
                    if self._should_roll(date, previous_date, market, position.contract(), signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, price))
                else:
                    band_offset = 4  # TODO load from params
                    upper_band = ma_short + band_offset * atr
                    lower_band = ma_short - band_offset * atr
                    previous_upper_band = previous_ma_short - band_offset * atr
                    previous_lower_band = previous_ma_short - band_offset * atr

                    if previous_price < previous_lower_band and price >= lower_band:
                        signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, price))
                    elif previous_price > previous_upper_band and price <= upper_band:
                        signals.append(Signal(market, SignalType.ENTER, Direction.SHORT, date, price))

        return signals
