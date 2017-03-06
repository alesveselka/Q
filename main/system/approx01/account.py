#!/usr/bin/python


class Account(object):  # TODO also simulate Cash, Margin, etc. to better reflect IB?

    def __init__(self, initial_balance):
        self.balance = initial_balance  # Update MTM, Cash, Bonds on new market data
