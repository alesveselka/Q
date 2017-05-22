import os
import MySQLdb as mysql


def study(name, window, window_name):
    return {'name': '%s_%s' % (name, window_name), 'study': 'ATR', 'window': window, 'columns': [
        'price_date',
        'high_price',
        'low_price',
        'settle_price'
    ]}

def simulations():
    studies = {
        'atr_100':
            {'name': 'atr_long', 'study': 'ATR', 'window': 'long_window', 'columns': [
                'price_date',
                'high_price',
                'low_price',
                'settle_price'
            ]},
        'atr_50':
            {'name': 'atr_short', 'study': 'ATR', 'window': 'short_window', 'columns': [
                'price_date',
                'high_price',
                'low_price',
                'settle_price'
            ]},
        'vol_50':
            {'name': 'vol_short', 'study': 'SMA', 'window': 'short_window', 'columns': [
                'price_date',
                'volume'
            ]},
        'sma_100':
            {'name': 'sma_long', 'study': 'SMA', 'window': 'long_window', 'columns': [
                'price_date',
                'settle_price'
            ]},
        'sma_50':
            {'name': 'sma_short', 'study': 'SMA', 'window': 'short_window', 'columns': [
                'price_date',
                'settle_price'
            ]},
        'hhll_50':
            {'name': 'hhll_short', 'study': 'HHLL', 'window': 'short_window', 'columns': [
                'price_date',
                'settle_price'
            ]}
    }
    sim = (
        'breakout_with_MA_filter_and_ATR_stop_1',
        {
            'risk_factor': 0.002,
            'commission': 10.0,
            'commission_currency': 'USD',
            'interest_minimums': {'AUD': 14000, 'CAD': 14000, 'CHF': 100000, 'EUR': 100000, 'GBP': 8000, 'JPY': 11000000, 'USD': 10000},
            'initial_balance': 1000000
        },
        'breakout_with_MA_filter_and_ATR_stop',
        {
            'short_window': 50,
            'long_window': 100,
            'filter_MA_type': 'SMA',
            'volatility_MA_type': 'SMA',
            'stop_multiple': 3,
            'stop_window': 50
        },
        studies,
        'standard_roll',
        '25Y'
    )


def insert_trading_models(values):
    with mysql_connection:
        cursor = mysql_connection.cursor()
        cursor.executemany("""INSERT INTO trading_model(name, description) VALUES (%s, %s)""", values)


if __name__ == '__main__':
    mysql_connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )
    trading_models = [(
        'breakout_with_MA_filter_and_ATR_stop',
        'Highest-high and Lowest-low breakout with Moving Average trend filter and ATR volatility based exit stops'
    )]
    insert_trading_models(trading_models)
