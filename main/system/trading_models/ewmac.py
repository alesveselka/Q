#!/usr/bin/python

from enum import Study
from enum import Direction
from enum import SignalType
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class EWMAC(TradingModel):
    """
    Exponential-Moving-Average Crossover (From the book Systematic Trading)
    
    Continuous signal is difference in between fast and slow EMAs, normalized with standard deviation of price, 
    and multiplied with 'Forecast scalar'.
    """

    def __init__(self, markets, params):
        self.__markets = markets
        self.__forecast_cap = 20

    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        signals = []

        # TODO load from params
        forecast_scalar = 3.75  # See table 49 (p. 285)

        for market in self.__markets:
            market_data, previous_data = market.data(date)

            if market.has_study_data() and market_data:
                previous_date = previous_data[Table.Market.PRICE_DATE]
                price = market_data[Table.Market.SETTLE_PRICE]
                ma_long = market.study(Study.MA_LONG, date)[Table.Study.VALUE]
                ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]
                variance = market.study(Study.PRICE_VARIANCE, date)[Table.Study.VALUE]
                stdev = variance ** 0.5
                raw_cross = ma_short - ma_long
                adjusted_cross = raw_cross / stdev
                forecast = adjusted_cross * forecast_scalar
                capped_forecast = -self.__forecast_cap if forecast < -self.__forecast_cap \
                    else (self.__forecast_cap if forecast > self.__forecast_cap else forecast)
                market_position = self._market_position(positions, market)

                if market_position:
                    direction = market_position.direction()
                    if self._should_roll(date, previous_date, market, market_position.contract(), signals):
                        signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, price))
                        signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, price))

                signals.append(Signal(market, SignalType.ENTER, Direction.LONG, date, price))

        return signals
