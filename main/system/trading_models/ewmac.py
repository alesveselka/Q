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
            if market.has_study_data():
                market_data, previous_data = market.data(date)
                forecast = self.__forecast(date, market, market_data, forecast_scalar)
                market_position = self._market_position(positions, market)

                if market_position:
                    if market_data:
                        price = market_data[Table.Market.SETTLE_PRICE]
                        previous_date = previous_data[Table.Market.PRICE_DATE]
                        direction = market_position.direction()
                        if self._should_roll(date, previous_date, market, market_position.contract(), signals):
                            signals.append(Signal(market, SignalType.ROLL_EXIT, direction, date, price))
                            signals.append(Signal(market, SignalType.ROLL_ENTER, direction, date, price, forecast))

                price = market_data[Table.Market.SETTLE_PRICE] if market_data \
                    else market.data_range(end_date=date)[-1][Table.Market.SETTLE_PRICE]
                direction = Direction.LONG if forecast >= 0 else Direction.SHORT
                signals.append(Signal(market, SignalType.ENTER, direction, date, price, forecast))

        return signals

    def __forecast(self, date, market, market_data, forecast_scalar):
        """
        Calculate trading signal forecast
        
        :param date:            date of the data
        :param market:          market to calculate forecast for
        :param market_data:     market data
        :param forecast_scalar: scalar to multiply signal with
        :return:                number representing final forecast value
        """
        if market_data is None:
            market_data_range = market.data_range(end_date=date)
            market_data = market_data_range[-1]

        date = market_data[Table.Market.PRICE_DATE]
        ma_long = market.study(Study.MA_LONG, date)[Table.Study.VALUE]
        ma_short = market.study(Study.MA_SHORT, date)[Table.Study.VALUE]
        variance = market.study(Study.PRICE_VARIANCE, date)[Table.Study.VALUE]
        stdev = variance ** 0.5
        raw_cross = ma_short - ma_long
        adjusted_cross = raw_cross / stdev
        forecast = adjusted_cross * forecast_scalar
        capped_forecast = -self.__forecast_cap if forecast < -self.__forecast_cap \
            else (self.__forecast_cap if forecast > self.__forecast_cap else forecast)

        return capped_forecast
