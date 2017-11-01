#!/usr/bin/python

from enum import Table
from series.market_series import MarketSeries


class NorgateSeries(MarketSeries):

    def __init__(self, start_data_date, study_parameters, roll_strategy, position_sizing, volatility_type, volatility_lookback, use_ew_correlation):
        super(NorgateSeries, self).__init__(
            start_data_date,
            study_parameters,
            roll_strategy,
            position_sizing,
            volatility_type,
            volatility_lookback,
            use_ew_correlation
        )

    def update_data(self, date):
        pass

    def load(self, connection, end_date, delivery_months, market_id, market_code, roll_strategy_id):
        """
        Load market's data

        :param connection:          MySQLdb connection instance
        :param end_date:            Last date to fetch data to
        :param delivery_months:     list of delivery months [(code, short-month-name)]
        :param market_id:           ID of the series market
        :param market_code:         code symbol of the series market
        :param roll_strategy_id:    ID of the series roll strategy
        """
        super(NorgateSeries, self).load(connection, end_date, delivery_months, market_id, market_code, roll_strategy_id)

        cursor = connection.cursor()
        continuous_query = """
            SELECT %s
            FROM %s
            WHERE market_id = '%s'
            AND code = '%s'
            AND roll_strategy_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
        cursor.execute(continuous_query % (
            self._column_names(),
            'continuous_adjusted',
            market_id,
            market_code,
            roll_strategy_id,
            self._start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        # This may cut 'weekend' dates, but those may be legit in markets in different time-zones (Asia, etc.)
        # TODO implement trading-hours to check properly
        workdays = range(1, 6)
        self._prices = [p for p in cursor.fetchall() if p[Table.Market.PRICE_DATE].isoweekday() in workdays]
        self._price_indexes = {i[1][Table.Market.PRICE_DATE]: i[0] for i in enumerate(self._prices)}

        return True

    # TODO actually implement margin multiplier, but with contract data?
    def margin(self, end_date, point_value):
        """
        Return calculated margin based on price and point value at the date passed in
        
        :param end_date:    date to calculate margin on
        :param point_value: point value of the market instrument
        :return:            number representing margin
        """
        return self._prices[-1][Table.Market.SETTLE_PRICE] * point_value * 0.1

    def contract(self, date):
        """
        Return 'None' since the continuous series doesn't have individual contracts
        
        :param date:    date by which find the contract
        :return:        contract symbol code 
        """
        return None

    def previous_contract(self, contract):
        """
        Return contract code before the one passed in
        
        :return:    string code representing the previous contract
        """
        return None

    def next_contract(self, contract):
        """
        Return contract code after the one passed in
        
        :return:    string code representing the next contract
        """
        return None

    def contract_data(self, contract, date):
        """
        Return data of contract passed in
        
        :return:    tuple representing one day record
        """
        return None

    def rolls(self):
        """
        Return empty list since the continuous series doesn't have roll data
        
        :return:    list of tuples(date, gap, roll-out-contract, roll-in-contract)
        """
        return []

    def scheduled_roll(self, date):
        """
        Return scheduled contract, if any
        
        :param date:    date of the roll
        :return string: contract symbol
        """
        return None
