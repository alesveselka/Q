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

    def __init__(self, markets, params, roll_strategy):
        self.__markets = markets
        self.__roll_strategy = roll_strategy  # TODO also move to super-class

    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        signals = []

        fast = 16
        slow = 64
        stdev_lookback = 36
        forecast_scalar = 3.75  # See table 49 (p. 285)
        fast_decay = 2.0 / (fast + 1)
        slow_decay = 2.0 / (slow + 1)
        stdev_decay = 2.0 / (stdev_lookback + 1)
        ewma_fast = []
        ewma_slow = []
        variance = []

        for market in self.__markets:
            market_data, previous_data = market.data(date)

            if market.has_study_data() and market_data:
                previous_date = previous_data[Table.Market.PRICE_DATE]
                previous_price = previous_data[Table.Market.SETTLE_PRICE]
                ma_long = market.study(Study.MA_LONG, date)[Table.Study.VALUE]
                ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]
                price = market_data[Table.Market.SETTLE_PRICE]
                market_position = self._market_position(positions, market)

                ret = price - previous_price
                ret_squared = previous_price**2
                if len(ewma_fast):
                    ewma_fast.append(fast_decay * price + (ewma_fast[-1] * (1 - fast_decay)))
                else:
                    ewma_fast.append(price)

                if len(ewma_slow):
                    ewma_slow.append(slow_decay * price + (ewma_slow[-1] * (1 - slow_decay)))
                else:
                    ewma_slow.append(price)

                if len(variance):
                    variance.append(stdev_decay * ret_squared + (variance[-1] * (1 - stdev_decay)))
                else:
                    variance.append(ret_squared)

                stdev = variance[-1] ** 0.5
                raw_cross = ewma_fast[-1] - ewma_slow[-1]
                adjusted_cross = raw_cross / stdev
                forecast = adjusted_cross * forecast_scalar
                capped_forecast = -20 if forecast < -20 else (20 if forecast > 20 else forecast)

        return signals
