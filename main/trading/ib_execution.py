#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import time
from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message
from event import FillEvent, OrderEvent
from execution import ExecutionHandler


class IBExecutionHandler(ExecutionHandler):
    """
    Handles order execution via the Interactive Brokers API,
    for use against accounts when trading live directly.
    """

    def __init__(self, events, order_routing='SMART', currency='USD'):
        """
        Initializes the IBExecutionHandler instance.
        """
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}

        self.tws_connection = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()
