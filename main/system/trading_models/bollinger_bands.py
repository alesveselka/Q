#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class BollingerBands(TradingModel):
    """
    'Bollinger Bands' model.
    
    Signal is generated against direction of trend, when price(Close) returns from outside back inside of the bands.
    """

    def __init__(self, name, markets, params):
        super(BollingerBands, self).__init__(name)
        self.__markets = markets
        self.__forecast = 10.0

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
                market_id = str(market.id())
                market_positions = {k.split('_')[1]: positions[k] for k in positions.keys() if k.split('_')[0] == market_id}
                market_position = market_positions.items()[0] if len(market_positions) else None

                price = market_data[Table.Market.SETTLE_PRICE]
                previous_date = previous_data[Table.Market.PRICE_DATE]
                previous_price = previous_data[Table.Market.SETTLE_PRICE]
                previous_ma_short = market.study(Study.MA_SHORT, previous_date)[Table.Study.VALUE]
                ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]

                if market_position:
                    position_contract = market_position[0]
                    position_quantity = market_position[1]
                    direction = Direction.LONG if position_quantity > 0 else Direction.SHORT
                    # Exit
                    if direction == Direction.LONG and previous_price < previous_ma_short and price >= ma_short:
                        signals.append(Signal(date, market, position_contract, 0, price))
                    elif direction == Direction.SHORT and previous_price > previous_ma_short and price <= ma_short:
                        signals.append(Signal(date, market, position_contract, 0, price))

                    if self._should_roll(date, previous_date, market, position_contract, signals):
                        # Roll
                        sign = 1 if position_quantity > 0 else -1
                        signals.append(Signal(date, market, position_contract, 0, price))
                        signals.append(Signal(date, market, market.contract(date), self.__forecast * sign, price))
                else:
                    atr = market.study(Study.ATR_SHORT, date)[Table.Study.VALUE]
                    band_offset = 4  # TODO load from params
                    upper_band = ma_short + band_offset * atr
                    lower_band = ma_short - band_offset * atr
                    previous_upper_band = previous_ma_short + band_offset * atr
                    previous_lower_band = previous_ma_short - band_offset * atr
                    contract = market.contract(date)
                    # Enter
                    if previous_price < previous_lower_band and price >= lower_band:
                        signals.append(Signal(date, market, contract, self.__forecast, price))
                    elif previous_price > previous_upper_band and price <= upper_band:
                        signals.append(Signal(date, market, contract, -self.__forecast, price))

        return signals
