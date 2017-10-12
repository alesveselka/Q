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


def update_simulation(simulation_id, column, value):
    cursor = mysql_connection.cursor()
    command = """UPDATE `simulation` SET `%s` = '%s' WHERE id = %s;"""
    cursor.execute(command % (column, value, simulation_id))
    mysql_connection.commit()


def studies(data):
    return [{'name': '%s_%s' % (d[0], d[1]), 'study': d[2], 'window': d[3], 'columns': d[4]} for d in data]


def roll_strategy_id(roll_strategy_name):
    cursor = mysql_connection.cursor()
    cursor.execute("""SELECT id, name FROM roll_strategy;""")
    return [r for r in cursor.fetchall() if r[1] == roll_strategy_name][0][0]


def __risk_params(position_sizing,
                  capital_correction,
                  partial_compounding_factor=0.25,
                  risk_factor=0.002,
                  volatility_target=0.2,
                  volatility_lookback=25,
                  use_ew=True,
                  group_weights=False):
    return {
        RISK_FACTOR: {
            'risk_factor': risk_factor,
            'position_inertia': 0.1,
            'use_position_inertia': False,
            'capital_correction': capital_correction,
            'partial_compounding_factor': partial_compounding_factor
        },
        EQUAL_WEIGHTS: {
            'volatility_target': volatility_target,
            'volatility_lookback': volatility_lookback,
            'volatility_type': 'movement',
            'position_inertia': 0.1,
            'use_position_inertia': True,
            'capital_correction': capital_correction,
            'partial_compounding_factor': partial_compounding_factor
        },
        CORRELATION_WEIGHTS: {
            'volatility_target': volatility_target,
            'volatility_lookback': volatility_lookback,
            'volatility_type': 'movement',
            'use_ew_correlation': use_ew,
            'use_group_correlation_weights': group_weights,
            'position_inertia': 0.1,
            'use_position_inertia': True,
            'capital_correction': capital_correction,
            'partial_compounding_factor': partial_compounding_factor
        }
    }[position_sizing]


def simulation_params(position_sizing, risk_params, initial_balance=1e6):
    # TODO also 'rebalance', 'long_only'
    # TODO also test 'USD' base currency and observe effect on margin interest
    return dict(risk_params.items() + {
        'initial_balance': initial_balance,
        'base_currency': 'EUR',
        'position_sizing': position_sizing,
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
    }.items())


def trading_params(model_name, stop_type):
    # TODO also use 'EMA' in volatility_MA_type
    return {
        TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP: {
            'short_window': 50,
            'long_window': 100,
            'filter_MA_type': 'SMA',
            'volatility_MA_type': 'SMA',
            'stop_multiple': 3,
            'stop_window': 50
        },
        TradingModel.PLUNGE_WITH_ATR_STOP_AND_PROFIT: {
            'short_window': 50,
            'long_window': 100,
            'filter_MA_type': 'EMA',
            'volatility_MA_type': 'SMA',
            'enter_multiple': 3,
            'stop_multiple': 2,
            'profit_multiple': 4,
            'stop_type': stop_type,  # fixed_stop, trailing_stop, time
            'stop_time': 30,
            'stop_window': 20
        },
        TradingModel.BOLLINGER_BANDS: {
            'short_window': 25,
            'long_window': 50,
            'filter_MA_type': 'EMA',
            'volatility_MA_type': 'EMA'
        },
        TradingModel.MA_TREND_ON_PULLBACK: {
            'short_window': 50,
            'long_window': 100,
            'filter_MA_type': 'SMA',
            'volatility_MA_type': 'SMA',
            'stop_multiple': 3,
            'stop_window': 50
        },
    }[model_name]


def study_map(model_name):
    return {
        TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP: studies([
            ('atr', 'long', 'ATR', 100, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('atr', 'short', 'ATR', 50, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('ma', 'long', 'SMA', 100, ['price_date', 'settle_price']),
            ('ma', 'short', 'SMA', 50, ['price_date', 'settle_price']),
            ('vol', 'short', 'SMA', 50, ['price_date', 'volume']),
            ('hhll', 'short', 'HHLL', 50, ['price_date', 'settle_price'])
        ]),
        TradingModel.PLUNGE_WITH_ATR_STOP_AND_PROFIT: studies([
            ('atr', 'long', 'ATR', 100, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('atr', 'short', 'ATR', 20, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('ma', 'long', 'EMA', 100, ['price_date', 'settle_price']),
            ('ma', 'short', 'EMA', 50, ['price_date', 'settle_price']),
            ('vol', 'short', 'SMA', 50, ['price_date', 'volume']),
            ('hhll', 'short', 'HHLL', 20, ['price_date', 'settle_price'])  # TODO 'Plunger' uses High and Low for extremes
        ]),
        TradingModel.BOLLINGER_BANDS: studies([
            ('atr', 'long', 'ATR', 25, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('atr', 'short', 'ATR', 25, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('ma', 'long', 'EMA', 50, ['price_date', 'settle_price']),
            ('ma', 'short', 'EMA', 25, ['price_date', 'settle_price']),
            ('vol', 'short', 'SMA', 25, ['price_date', 'volume'])
        ]),
        TradingModel.MA_TREND_ON_PULLBACK: studies([
            ('atr', 'long', 'ATR', 100, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('atr', 'short', 'ATR', 50, ['price_date', 'high_price', 'low_price', 'settle_price']),
            ('ma', 'long', 'SMA', 100, ['price_date', 'settle_price']),
            ('ma', 'short', 'SMA', 50, ['price_date', 'settle_price']),
            ('vol', 'short', 'SMA', 50, ['price_date', 'volume'])
        ]),
    }[model_name]


def simulation(trading_model, variation, params, roll_strategy_name, stop_type='trailing_stop', investment_universe='25Y'):
    return (
        '%s_%s' % (trading_model, variation),
        json.dumps(params),
        trading_model,
        json.dumps(trading_params(trading_model, stop_type)),
        json.dumps(study_map(trading_model)),
        roll_strategy_id(roll_strategy_name),
        investment_universe
    )


def simulations():
    # TODO buy_and_hold (w/ rebalance)
    return [
        # Breakout with MA filter and ATR stop
        simulation(
            TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP, '1',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING)),
            'norgate'
        ),
        simulation(
            TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP, '2',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING)),
            'standard_roll_1'
        ),
        simulation(
            TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP, '3',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING)),
            'optimal_roll_1'
        ),
        simulation(
            TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP, '4',
            simulation_params(EQUAL_WEIGHTS, __risk_params(EQUAL_WEIGHTS, FULL_COMPOUNDING), initial_balance=1e7),
            'standard_roll_1'
        ),

        # Plunge with ATR stop and profit target
        simulation(
            TradingModel.PLUNGE_WITH_ATR_STOP_AND_PROFIT, '1',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING, 0.25, 0.001)),
            'standard_roll_1',
            'fixed_stop'
        ),
        simulation(
            TradingModel.PLUNGE_WITH_ATR_STOP_AND_PROFIT, '2',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING, 0.25, 0.001)),
            'standard_roll_1',
            'time'
        ),
        simulation(
            TradingModel.PLUNGE_WITH_ATR_STOP_AND_PROFIT, '3',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING, 0.25, 0.001)),
            'standard_roll_1'
        ),

        # Bollinger Bands
        simulation(
            TradingModel.BOLLINGER_BANDS, '1',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING)),
            'standard_roll_1'
        ),

        # MA Trend on Pull-back
        simulation(
            TradingModel.MA_TREND_ON_PULLBACK, '1',
            simulation_params(RISK_FACTOR, __risk_params(RISK_FACTOR, FULL_COMPOUNDING)),
            'standard_roll_1'
        ),
    ]


class TradingModel:
    BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP = 'breakout_with_MA_filter_and_ATR_stop'
    PLUNGE_WITH_ATR_STOP_AND_PROFIT = 'plunge_with_ATR_stop_and_profit'
    BOLLINGER_BANDS = 'bollinger_bands'
    MA_TREND_ON_PULLBACK = 'ma_trend_on_pullback'


if __name__ == '__main__':
    mysql_connection = mysql.connect(
        os.environ['DB_HOST'],
        os.environ['DB_USER'],
        os.environ['DB_PASS'],
        os.environ['DB_NAME']
    )
    trading_models = {
        TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP: {
            'name': TradingModel.BREAKOUT_WITH_MA_FILTER_AND_ATR_STOP,
            'desc': 'Highest-high and Lowest-low breakout with Moving Average trend filter and ATR volatility based exit stops'
        },
        TradingModel.PLUNGE_WITH_ATR_STOP_AND_PROFIT: {
            'name': TradingModel.PLUNGE_WITH_ATR_STOP_AND_PROFIT,
            'desc': 'Enter into trend after price reverse from trend-direction for x-amount of ATR'
        },
        TradingModel.BOLLINGER_BANDS: {
            'name': TradingModel.BOLLINGER_BANDS,
            'desc': 'Enter against trend after price returns back inside the Bollinger bands'
        },
        TradingModel.MA_TREND_ON_PULLBACK: {
            'name': TradingModel.MA_TREND_ON_PULLBACK,
            'desc': 'Enter in direction of a trend defined by MA cross, when price pull back to the shorter MA'
        }
    }
    RISK_FACTOR = 'risk_factor'
    EQUAL_WEIGHTS = 'volatility_target_equal_weights'
    CORRELATION_WEIGHTS = 'volatility_target_correlation_weights'
    FIXED = 'fixed'
    FULL_COMPOUNDING = 'full_compounding'
    HALF_COMPOUNDING = 'half_compounding'
    PARTIAL_COMPOUNDING = 'partial_compounding'

    # trading_model = trading_models[TradingModel.MA_TREND_ON_PULLBACK]
    # insert_trading_models([(trading_model['name'], trading_model['desc'])])
    # insert_simulations([simulations()[-1]])
    # update_simulation(16, 'params', simulations()[6][1])
