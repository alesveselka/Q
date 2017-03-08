#!/usr/bin/python

from decimal import Decimal


def HHLL(data, window):
    """
    Highest High and Lowest Low
    """
    _max = 0
    _min = 0
    for i, d in enumerate(data):
        start = i + 1 - 50 if i + 1 >= 50 else 0
        settle_prices = [d[5] for d in data[start:i+1]]
        print d[1], start, i, len(settle_prices), settle_prices[-1], _max, _min

        # if len(settle_prices) == 50:
        #     if settle_prices[-1] >= _max:
        #         print 'LONG'
        #     elif settle_prices[-1] <= _min:
        #         print 'SHORT'

        _max = max(settle_prices)  # TODO pass in NaN if there is not enough days?
        _min = min(settle_prices)

        # self.__data.append((d[1], max(), min()))


def SMA(data, window):
    """
    Simple Moving Average

    :param data:    List of data to compute the SMA on.
                    Each item is tuple with two items - first is date, second actual value
    :param window:  The size of 'moving window'
    :return:        List of tuples with two items - first date, and second computed value
    """
    w = Decimal(window)
    nones = [(d[0], None) for d in data[:window]]
    dates, values = zip(*data)
    smas = [(dates[i], sum(values[i-window:i]) / w) for i in range(window, len(data))]
    return nones + smas


def EMA(data, window):
    """
    Exponential Moving Average
    https://www.oanda.com/forex-trading/learn/forex-indicators/exponential-moving-average

    :param data:    List of data to compute the EMA on.
                    Each item is tuple with two items - first is date, second actual value
    :param window:  The size of 'moving window'
    :return:        List of tuples with two items - first date, and second computed value
    """
    ema = None

    for i, d in enumerate(data):
        start = i + 1 - window if i + 1 >= window else 0
        settle_prices = [d[5] for d in data[start:i+1]]
        sma = sum(settle_prices) / Decimal(len(settle_prices))
        c = Decimal(2.0 / (len(settle_prices) + 1))
        # TODO the above is not needed to calculate every iteration
        ema = (c * settle_prices[-1]) + ((1 - c) * (ema or sma))
        print d[1], start, i, len(settle_prices), settle_prices[-1], sma, ema


def ATR(data, window):
    print 'atr'
