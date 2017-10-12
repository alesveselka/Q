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

    def __init__(self, markets, params):
        self.__markets = markets

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
                market_position = self._market_position(positions, market)

                if market_position:
                    direction = market_position.direction()
                    if self._should_roll(date, previous_date, market, market_position.contract(), signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, price))

                signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, price))

        return signals
