#!/usr/bin/python


def HHLL(data, window):
    """
    Highest High and Lowest Low
    Calculated data include the latest data in the window

    :param data:    List of tuples(date, value) to compute the HH and LL on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, highest-high value, lowest-low value)
    """
    # TODO split into 'highest' and 'lowest' to unify (date, value) structure among studies and save them to DB
    # TODO speed up similar to SMA!
    dates, values = zip(*data)
    return [(dates[i], max(values[i-window+1:i+1]), min(values[i-window+1:i+1])) for i in range(window-1, len(data))]


def SMA(data, window):
    """
    Simple Moving Average
    Calculated data include the latest data in the window

    :param data:    List of tuples(date, value) to compute the SMA on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    dates, values = zip(*data)
    s = 0.0
    smas = []
    for i in range(0, window):
        s += values[i]
        smas.append((dates[i], s / (i + 1)))

    for i in range(window, len(values)):
        s = s - values[i - window] + values[i]
        smas.append((dates[i], s / window))

    return smas[window-1:]


def EMA(data, window):
    """
    Exponential Moving Average
    https://www.oanda.com/forex-trading/learn/forex-indicators/exponential-moving-average
    Calculated data include the latest data in the window

    :param data:    List of tuples(date, value) to compute the EMA on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    dates, values = zip(*data)
    c = 2.0 / (window + 1)
    ma = SMA(data[:window], window)[-1]
    emas = []
    for i in range(window-1, len(data)):
        ma = (dates[i], (c * values[i]) + (1 - c) * ma[1])
        emas.append(ma)

    return emas


def ATR(data, window):
    """
    Average True Range
    Calculated data include the latest data in the window.
    It needs one more day of data to calculate due to TR calculations

    :param data:    List of tuples(date, high-value, low-value, last-value) to compute the ATR on.
    :param window:  The size of 'moving window'
    :return:        List of tuples(date, value)
    """
    tr = [(item[0], max(item[1], data[i][3]) - min(item[2], data[i][3])) for i, item in enumerate(data[1:])]
    return EMA(tr, window)
