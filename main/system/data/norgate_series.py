#!/usr/bin/python

from enum import Table
from data.market_series import MarketSeries


class NorgateSeries(MarketSeries):

    def __init__(self, start_data_date, study_parameters):
        super(NorgateSeries, self).__init__(start_data_date, study_parameters)

        # self.__roll_strategy_id = roll_strategy_id

    def update_data(self, date):
        """
        Update dynamic data
        
        :param date:    date of the data update
        """
        pass

    def load(self, connection, end_date, delivery_months, market_id, market_code):
        """
        Load market's data

        :param connection:          MySQLdb connection instance
        :param end_date:            Last date to fetch data to
        :param delivery_months:     list of delivery months [(code, short-month-name)]
        """
        super(NorgateSeries, self).load(connection, end_date, delivery_months, market_id, market_code)

        # TODO use connection pool?
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
            2,  #self.__roll_strategy_id,
            self._start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        # TODO I can make a generator and retrieve the data when needed
        self._prices = cursor.fetchall()
        self._price_indexes = {i[1][Table.Market.PRICE_DATE]: i[0] for i in enumerate(self._prices)}

        return True

    # TODO move elsewhere
    # TODO actually implement margin multiplier, but with contract data?
    def margin(self, end_date, point_value):
        return self._prices[-1][Table.Market.SETTLE_PRICE] * point_value * 0.1
