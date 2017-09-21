#!/usr/bin/python

import csv
import datetime as dt


class MarketCorrelationProxy:

    def __init__(self):
        pass

    @staticmethod
    def from_db(connection, market_id, market_code, start_date, end_date, volatility_type, volatility_lookback, use_ew_correlation):
        """
        Load and return correlation data from files
        
        :param connection:          DB connection
        :param market_id:           ID of the market to load
        :param market_code:         Code of the market to load
        :param start_date:          start date if the data
        :param end_date:            end date of the data
        :param volatility_type:     type of the volatility to load (either 'movement' or 'dev'(deviation))
        :param volatility_lookback: number of days used for the volatility calculation lookback
        :param use_ew_correlation:  boolean value to indicate if EW series should be used or not
        :return:                    tuple of
                                        list of correlation data and
                                        dict of indexes with dates as keys
        """
        cursor = connection.cursor()
        correlation_query = """
            SELECT date, %s_volatility, %s_correlations%s
            FROM market_correlation
            WHERE market_id = '%s'
            AND market_code = '%s'
            AND lookback = '%s'
            AND DATE(date) >= '%s'
            AND DATE(date) <= '%s'
            ORDER BY date;
        """
        cursor.execute(correlation_query % (
            volatility_type,
            volatility_type,
            '_ew' if use_ew_correlation else '',
            market_id,
            market_code,
            str(volatility_lookback),
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        correlation_data = cursor.fetchall()

        workdays = range(1, 6)
        correlations = [p for p in correlation_data if p[0].isoweekday() in workdays]
        correlation_indexes = {i[1][0]: i[0] for i in enumerate(correlations)}

        return correlations, correlation_indexes

    @staticmethod
    def from_files(market_code, lookback, start_date, end_date):
        """
        Load and return correlation data from files
        
        :param market_code:     Code of the market to load
        :param lookback:        lookback constant used in computing the data
        :param start_date:      start date if the data
        :param end_date:        end date of the data
        :return:                tuple of
                                    list of correlation data and
                                    dict of indexes with dates as keys
        """
        reader = csv.reader(open('./db/market_correlation/%s/%s.csv' % (lookback, market_code)), delimiter=',', quotechar="'")
        rows = [(dt.date(*map(int, r[0].split('-'))), float(r[1]), r[2]) for r in reader]

        workdays = range(1, 6)
        correlations = sorted([p for p in rows if start_date <= p[0] <= end_date and p[0].isoweekday() in workdays])
        correlation_indexes = {i[1][0]: i[0] for i in enumerate(correlations)}

        return correlations, correlation_indexes

    @staticmethod
    def dump(market_code, lookback, correlations):
        f = open('./db/market_correlation/%s/%s.csv' % (lookback, market_code), 'w')
        f.write('\n'.join(["%s,%s,'%s'" % (str(c[0]), str(c[1]), c[2]) for c in correlations]))
        f.close()
