#!/usr/bin/python

from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class BuyAndHold(TradingModel):
    """
    Buy and Hold.
    
    Enter signal is at beginning of each market price series -- simply enter long each market 
    and holds it till end of simulation.
    No exits. Positions will rebalance with each contract roll.
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
                previous_date = previous_data[Table.Market.PRICE_DATE]
                price = market_data[Table.Market.SETTLE_PRICE]
                market_position = self.__market_position(positions, market)

                if market_position:
                    direction = market_position.direction()
                    if self.__should_roll(date, previous_date, market, market_position.contract(), signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, price))

                signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, price))

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

    def __market_position(self, positions, market):
        """
        Find and return position by market passed in
        
        :param positions:   list of open positions
        :param market:      Market to filter by
        :return:            Position object
        """
        positions = [p for p in positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None
