#!/usr/bin/python

from enum import Study
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
        self.__params = params
        self.__forecast_cap = params['forecast_cap']
        self.__forecast_scalar = self.__params['forecast_scalar']

    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        signals = []

        for market in self.__markets:
            market_data, previous_data = market.data(date)

            if market_data and market.has_study_data():
                market_id = str(market.id())
                market_positions = {k.split('_')[1]: positions[k] for k in positions.keys() if k.split('_')[0] == market_id}
                market_position = market_positions.items()[0] if len(market_positions) else None
                forecast = self.__forecast(date, market, market_data)

                if market_position:
                    price = market_data[Table.Market.SETTLE_PRICE]
                    previous_date = previous_data[Table.Market.PRICE_DATE]
                    position_contract = market_position[0]
                    # Roll
                    if self._should_roll(date, previous_date, market, position_contract, signals):
                        signals.append(Signal(date, market, position_contract, 0, price))
                        signals.append(Signal(date, market, market.contract(date), forecast, price))

                if not len(signals):
                    price = market_data[Table.Market.SETTLE_PRICE] if market_data \
                        else market.data_range(end_date=date)[-1][Table.Market.SETTLE_PRICE]
                    signals.append(Signal(date, market, market.contract(date), forecast, price))

        return signals

    def __forecast(self, date, market, market_data):
        """
        Calculate trading signal forecast
        
        :param date:            date of the data
        :param market:          market to calculate forecast for
        :param market_data:     market data
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
        forecast = adjusted_cross * self.__forecast_scalar
        capped_forecast = -self.__forecast_cap if forecast < -self.__forecast_cap \
            else (self.__forecast_cap if forecast > self.__forecast_cap else forecast)

        return capped_forecast
