#!/usr/bin/python

from enum import EventType
from event_dispatcher import EventDispatcher


class TradingSystem(EventDispatcher):

    def __init__(self, investment_universe):
        super(TradingSystem, self).__init__()

        self.__investment_universe = investment_universe

        self.__register_event_listeners()

    def __register_event_listeners(self):
        self.__investment_universe.on(EventType.MARKET_DATA, self.__on_market_data)

    def __on_market_data(self, data):
        print '_on_market_data:'
