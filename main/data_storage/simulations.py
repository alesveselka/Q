import os
import json
import MySQLdb as mysql


def insert_trading_models(values):
    with mysql_connection:
        cursor = mysql_connection.cursor()
        cursor.executemany('INSERT INTO trading_model(name, description) VALUES (%s, %s)', values)


def insert_simulations(values):
    columns = ['name', 'params', 'trading_model', 'trading_params', 'studies', 'roll_strategy_id', 'investment_universe']
    command = 'INSERT INTO `simulation` (%s) VALUES(%s)' % (', '.join(columns), ('%s, ' * len(columns))[:-2])

    with mysql_connection:
        cursor = mysql_connection.cursor()
        cursor.executemany(command, values)


def studies(data):
    return [{'name': '%s_%s' % (d[0], d[1]), 'study': d[2], 'window': d[3], 'columns': d[4]} for d in data]


def simulation_params(initial_balance, risk_factor):
    return {
        'initial_balance': initial_balance,
        'base_currency': 'EUR',
        'risk_factor': risk_factor,
        'commission': 10.0,
        'commission_currency': 'USD',
        'interest_minimums': {
            'AUD': 14000,
            'CAD': 14000,
            'CHF': 100000,
            'EUR': 100000,
            'GBP': 8000,
            'JPY': 11000000,
            'USD': 10000
        },
        'slippage_map': [
            {'atr': 2, 'min': 0, 'max': 100},
            {'atr': 1, 'min': 100, 'max': 1000},
            {'atr': 0.25, 'min': 1000, 'max': 10000},
            {'atr': 0.1, 'min': 10000, 'max': 50000},
            {'atr': 0.05, 'min': 50000, 'max': 200000},
            {'atr': 0.01, 'min': 200000, 'max': 1e9}
        ]
    }


def simulations():
    trading_model_name = trading_model_data[0][0]
    trading_params = {
        'short_window': 50,
        'long_window': 100,
        'filter_MA_type': 'SMA',
        'volatility_MA_type': 'SMA',
        'stop_multiple': 3,
        'stop_window': 50
    }
    study_map = studies([
        ('atr', 'long', 'ATR', 100, ['price_date', 'high_price', 'low_price', 'settle_price']),
        ('atr', 'short', 'ATR', 50, ['price_date', 'high_price', 'low_price', 'settle_price']),
        ('ma', 'long', 'SMA', 100, ['price_date', 'settle_price']),
        ('ma', 'short', 'SMA', 50, ['price_date', 'settle_price']),
        ('vol', 'short', 'SMA', 50, ['price_date', 'volume']),
        ('hhll', 'short', 'HHLL', 50, ['price_date', 'settle_price'])
    ])
    return [(
        '%s_1' % trading_model_name,
        json.dumps(simulation_params(1e6, 0.002)),
        trading_model_name,
        json.dumps(trading_params),
        json.dumps(study_map),
        0,
        '25Y'
    )]


if __name__ == '__main__':
    mysql_connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )
    trading_model_data = [(
        'breakout_with_MA_filter_and_ATR_stop',
        'Highest-high and Lowest-low breakout with Moving Average trend filter and ATR volatility based exit stops'
    )]
    # insert_trading_models(trading_model_data)
    insert_simulations(simulations())
