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

    def __error_handler(self, message):
        """
        Handles the capturing of error messages.
        """
        print "Server Error: %s" % message

    def __reply_handler(self, message):
        """
        Handles server replies.
        """
        # Handle open order orderId processing
        if message.typeName == 'openOrder' and \
           message.orderId == self.order_id and \
           not self.fill_dict.has_key(message.orderId):
            self.create_fill_dict_entry(message)
        # Handle fills
        if message.typeName == 'orderStatus' and \
           message.status == 'Filled' and \
           self.fill_dict[message.orderId]['filled'] == False:
            self.create_fill(message)

        print "Server Response: %s, %s\n" % (message.typeName, message)

    def create_tws_connection(self):
        """
        Connect to the Trader Workstation (TWS) running on
        the usual port 7496, with a cliendId of 10. The cliendId 
        is chosen by us and we will need separate IDs for both 
        the execution connection and market data connection, 
        if the latter is used elsewhere.
        """
        tws_connection = ibConnection()
        tws_connection.connect()
        return tws_connection

    def create_initial_order_id(self):
        """
        Creates the initial order ID used for Interactive Brokers 
        to keep track of submitted orders.
        """
        # There is scope for more login here, 
        # but we will use '1' as the default for now.
        return 1

    def register_handlers(self):
        """
        Register the error and server reply
        message handling functions.
        """
        # Assign the error handling function defined above
        # to the TWS connection
        self.tws_connection.register(self.__error_handler, 'Error')

        # Assign all of the server reply messages to
        # the '__reply_handler' function defined above
        self.tws_connection.registerAll(self.__reply_handler)

    def create_contract(self, symbol, sec_type, exch, prim_exch, curr):
        """
        Create a Contract object defining what will be purchased,
        at which exchange and in which currency.

        Parameters:
        symbol      The ticker symbol for the contract
        sec_type    The security type for the contract ('STK' is 'stock')
        exch        The exchange to carry out the contract on
        prim_exch   The primary exchange to carry out the contract on
        curr        The currency in which to purchase the contract
        """
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_sectype = sec_type
        contract.m_exchange = exch
        contract.m_primaryExch = prim_exch
        contract.m_currency = curr
        return contract

    def create_order(self, order_type, quantity, action):
        """
        Create an Order object (Market/Limit) to go long/short.

        Parameters:
        order_type  'MKT' or 'LMT' for Market or Limit orders.
        quantity    Integral number of assets to order.
        action      'BUY' or 'SELL'
        """
        order = Order()
        order.m_orderType = order_type
        order.m_totalQuantity = quantity
        order.m_action = action
        return order

    def create_fill_dict_entry(self, message):
        """
        Creates an entry in Fill dictionary that lists
        orderIds and provides security  information. This
        is needed for the event-driven behavior of the IB 
        server message behavior.
        """
        self.fill_dict[message.orderId] = {
            "symbol": message.contract.m_symbol,
            "exchange": message.contract.m_exchange,
            "direction": message.contract.m_action,
            "filled": False
        }

    def create_fill(self, message):
        """
        Handles the creation of the FillEvent that will be 
        placed onto the event queue subsequent to an order
        being filled.
        """
        fd = self.fill_dict[message.orderId]

        # Prepare the fill data
        symbol = fd['symbol']
        exchange = fd['exchange']
        filled = message.filled
        direction = fd['direction']
        fill_cost = message.avgFillPrice

        # Create a fill event object
        fill_event = FillEvent(
            dt.datetime.utcnow(), symbol, 
            exchange, filled, direction, fill_cost
        )

        # Make sure that multiple messages don't create
        # additional fills
        self.fill_dict[message.orderId]['filled'] = True

        # Place the fill event onto the event queue
        self.events.put(fill_event)

    def execute_order(self, event):
        """
        Creates the necessary InteractiveBrokers order object
        and submits it to IB via their API.

        The results are then queried in order to generate
        a corresponding Fill object, which is placed back on 
        the event queue.

        Parameters:
        event   Contains an Event object with order information.
        """
        if event.type == 'ORDER':
            # Prepare the parameters for the asset order
            asset = event.symbol
            asset_type = 'STK'
            order_type = event.order_type
            quantity = event.quantity
            direction = event.direction

            # Create the Interactive Brokers contract
            # via the passed Order event
            ib_contract = self.create_contract(
                asset, asset_type, self.order_routing,
                self.order_routing, self.currency
            )

            # Create the Interactive Brokers order
            # via the passed Order event
            ib_order = self.create_order(
                order_type, quantity, direction
            )

            # Use the connection to send the order to IB
            self.tws_connection.placeOrder(
                self.order_id, ib_contract, ib_order
            )

            # NOTE: This following line is crucial.
            # It ensures the order goes through!
            time.sleep(1)

            # Increment the order ID for this session
            self.order_id += 1
