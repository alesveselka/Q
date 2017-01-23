#!/usr/bin/python
# -*- coding: utf-8 -*-

class Event(object):
    """
    Event is base class providing an interface for all
    subsequent (inherited) events, that will trigger further 
    events in the trading infrastructure.
    """
    pass


class MarketEvent(Event):
    """
    Handles the event of receiving a new market update
    with corresponding bars.
    """

    def __init__(self):
        """
        Initialises the MarketEvent.
        """
        self.type = 'MARKET'


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """

    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        """
        Initialises the SignalEvent.

        Parameters:
        strategy_id     The unique identifier for the strategy that
                        generated the signal.
        symbol          The ticker symbol, e.g. 'GOOG'
        datetime        The timestamp at which  the signal was generated.
        signal_type     'LONG' or 'SHORT'.
        strength        An adjustment factor 'suggestion' used to scale
                        quantity at the portfolio level. Useful for
                        pairs strategies.
        """
        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class OrderEvent(Event):
    """
    Handles the event of sending and Order to an execution system.
    The order contains a symbol (e.g. 'GOOG'), a type (market or limit),
    quantity and a direction.
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        Initialises the OrderEvent, setting whether it is a Market 
        order ('MKT') or Limit order ('LMT'), has a quantity (integral) 
        and its direction ('BUY' or 'SELL').

        Parameters:
        symbol      The instrument to trade.
        order_type  'MKT' or 'LMT' for Market or Limit.
        quantity    Non-negative integer for quantity.
        direction   'BUY' or 'SELL' for long or short.
        """
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        """
        Outputs the values within the Order.
        """
        print 'Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s' %
              (self.symbol, self.type, self.quantity, self.direction)
