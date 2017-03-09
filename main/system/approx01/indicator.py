#!/usr/bin/python

from decimal import Decimal


def HHLL(data, window):
    """
    Highest High and Lowest Low

    :param data:    List of tuples(date, value) to compute the HH and LL on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, highest-high value, lowest-low value)
    """
    dates, values = zip(*data)
    return [(dates[i], max(values[i-window:i]), min(values[i-window:i])) for i in range(window, len(data))]


def SMA(data, window):
    """
    Simple Moving Average

    :param data:    List of tuples(date, value) to compute the SMA on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    w = Decimal(window)
    # nones = [(d[0], None) for d in data[:window]]
    dates, values = zip(*data)
    smas = [(dates[i], sum(values[i-window:i]) / w) for i in range(window, len(data))]
    # return nones + smas
    return smas


def EMA(data, window):
    """
    Exponential Moving Average
    https://www.oanda.com/forex-trading/learn/forex-indicators/exponential-moving-average

    :param data:    List of tuples(date, value) to compute the EMA on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    dates, values = zip(*data)
    c = Decimal(2.0 / (window + 1))
    ma = SMA(data[:window+1], window)[-1]
    emas = []
    for i in range(window, len(data)):
        ma = (dates[i], (c * values[i]) + (1 - c) * Decimal(ma[1]))
        emas.append(ma)

    return emas

    # print '*****************************************'
    # ema = None
    #
    # for i, d in enumerate(data):
    #     start = i + 1 - window if i + 1 >= window else 0
    #     settle_prices = [d[1] for d in data[start:i+1]]
    #     sma = sum(settle_prices) / Decimal(len(settle_prices))
    #     c = Decimal(2.0 / (len(settle_prices) + 1))
    #     # TODO the above is not needed to calculate every iteration
    #     ema = (c * settle_prices[-1]) + ((1 - c) * (ema or sma))
    #     print d[0], start, i, len(settle_prices), settle_prices[-1], sma, ema


def ATR(data, window):
    """
    Average True Range

    :param data:    List of tuples(date, value) to compute the ATR on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    print 'atr'
