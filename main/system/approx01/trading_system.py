#!/usr/bin/python


class TradingSystem(object):

    def __init__(self, investment_universe):
        self._investment_universe = investment_universe
        self.signals = []
