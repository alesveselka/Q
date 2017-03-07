#!/usr/bin/python

from decimal import Decimal


class Study(object):

    def __init__(self, market):
        self.__market = market
        self.__data = []

    def calculate(self, data):
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

    def sma(self, data, window):
        """
        Calculates Simple Moving Average
        http://fxtrade.oanda.com/learn/forex-indicators/simple-moving-average
        """
        if len(data) < window:
            return None

        return sum(data[-window:]) / Decimal(window)

    def calculate2(self, data):
        window = 50
        ema = None

        for i, d in enumerate(data):
            start = i + 1 - window if i + 1 >= window else 0
            settle_prices = [d[5] for d in data[start:i+1]]
            sma = sum(settle_prices) / Decimal(len(settle_prices))
            c = Decimal(2.0 / (len(settle_prices) + 1))
            # TODO the above is not needed to calculate every iteration
            ema = (c * settle_prices[-1]) + ((1 - c) * (ema or sma))
            print d[1], start, i, len(settle_prices), settle_prices[-1], sma, ema

        # if len(settle_prices) < 2 * window:
        #     raise ValueError("data is too short")
        # c = Decimal(2.0 / (window + 1))
        # current_ema = self.sma(settle_prices[-window*2:-window], window)
        # # for i, d in enumerate(data[-window:]):
        # for i, d in enumerate(data):
        #     current_ema = (c * d[5]) + ((1 - c) * current_ema)
        #     print d[1], i, d[5], current_ema
