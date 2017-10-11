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
                position = self.__market_position(positions, market)
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
                    if self.__should_roll(date, previous_date, market, position.contract(), signals):
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
    def __market_position(self, positions, market):
        """
        Find and return position by market passed in
        
        :param positions:   list of open positions
        :param market:      Market to filter by
        :return:            Position object
        """
        positions = [p for p in positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None
