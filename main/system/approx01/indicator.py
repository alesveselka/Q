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
    return [(dates[i], max(values[i-window+1:i+1]), min(values[i-window+1:i+1])) for i in range(window-1, len(data))]


def SMA(data, window):
    """
    Simple Moving Average

    :param data:    List of tuples(date, value) to compute the SMA on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    w = Decimal(window)
    dates, values = zip(*data)
    return [(dates[i], sum(values[i-window+1:i+1]) / w) for i in range(window-1, len(data))]


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
    ma = SMA(data[:window], window)[-1]
    emas = []
    for i in range(window-1, len(data)):
        ma = (dates[i], (c * values[i]) + (1 - c) * Decimal(ma[1]))
        emas.append(ma)

    return emas


def ATR(data, window):
    """
    Average True Range

    :param data:    List of tuples(date, high-value, low-value, last-value) to compute the ATR on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    w = Decimal(window)
    tr = [(item[0], max(item[1], data[i][3]) - min(item[2], data[i][3])) for i, item in enumerate(data[1:])]
    dates, values = zip(*tr)
    return [(dates[i], sum(values[i-window+1:i+1]) / w) for i in range(window-1, len(tr))]
