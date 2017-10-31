#!/usr/bin/python

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

    def __init__(self, name, markets, params):
        super(BuyAndHold, self).__init__(name)
        self.__markets = markets
        self.__forecast = 10.0  # TODO load from params

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

                if market_position:
                    position_contract = market_position[0]
                    position_quantity = market_position[1]
                    previous_date = previous_data[Table.Market.PRICE_DATE]
                    if self._should_roll(date, previous_date, market, position_contract, signals):
                        sign = 1 if position_quantity > 0 else -1
                        signals.append(Signal(date, market, position_contract, 0, price))
                        signals.append(Signal(date, market, market.contract(date), self.__forecast * sign, price))
                else:
                    signals.append(Signal(date, market, market.contract(date), self.__forecast, price))

        return signals
