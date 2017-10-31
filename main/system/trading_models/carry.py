#!/usr/bin/python

from collections import deque
from enum import Study
from enum import Table
from strategy_signal import Signal
from trading_models.trading_model import TradingModel


class CARRY(TradingModel):
    """
    Capture difference in contract prices. (From the book Systematic Trading)
    
    Continuous signal is annualised and volatility-normalised difference between prices of two contracts 
    and multiplied with 'Forecast scalar'.
    """

    def __init__(self, name, markets, params):
        super(CARRY, self).__init__(name)
        self.__markets = markets
        self.__params = params
        self.__forecast_cap = params['forecast_cap']
        self.__forecast_scalar = self.__params['forecast_scalar']
        self.__root_days_in_year = 256 ** 0.5
        self.__recent_forecasts = deque([], 5)

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
                self.__recent_forecasts.append(forecast)
                avg_forecast = sum(self.__recent_forecasts) / len(self.__recent_forecasts)
                contract = market.contract(date)

                if market_position:
                    price = market_data[Table.Market.SETTLE_PRICE]
                    previous_date = previous_data[Table.Market.PRICE_DATE]
                    position_contract = market_position[0]
                    # Roll
                    if self._should_roll(date, previous_date, market, position_contract, signals):
                        signals.append(Signal(date, market, position_contract, 0, price))
                        signals.append(Signal(date, market, contract, avg_forecast, price))

                if not len([s for s in signals if s.market() == market and s.contract() == contract]):
                    price = market_data[Table.Market.SETTLE_PRICE] if market_data \
                        else market.data_range(end_date=date)[-1][Table.Market.SETTLE_PRICE]
                    signals.append(Signal(date, market, contract, avg_forecast, price))

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
        contract = market_data[Table.Market.CODE]
        contract_data = market.contract_data(contract, date)
        price = contract_data[Table.Market.SETTLE_PRICE]

        previous_contract = market.previous_contract(contract)
        previous_contract_data = market.contract_data(previous_contract, date)

        if previous_contract_data:
            distance = market.contract_distance(previous_contract, contract)
            price_diff = price - previous_contract_data[Table.Market.SETTLE_PRICE]
        else:
            next_contract = market.next_contract(contract)
            next_contract_data = market.contract_data(next_contract, date)
            distance = market.contract_distance(contract, next_contract) if next_contract else 0.0
            price_diff = (next_contract_data[Table.Market.SETTLE_PRICE] - price) if next_contract_data else 0.0

        expected_return = price_diff / distance if distance else 0.0
        variance = market.study(Study.PRICE_VARIANCE, date)[Table.Study.VALUE]
        stdev = (variance ** 0.5) * self.__root_days_in_year
        raw_carry = expected_return / stdev
        forecast = raw_carry * self.__forecast_scalar
        capped_forecast = -self.__forecast_cap if forecast < -self.__forecast_cap \
            else (self.__forecast_cap if forecast > self.__forecast_cap else forecast)

        return capped_forecast
