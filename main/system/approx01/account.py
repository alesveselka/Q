#!/usr/bin/python


class Account(object):  # TODO also simulate Cash, Margin, etc. to better reflect IB?

    def __init__(self):
        self.balance = 0  # Update MTM, Cash, Bonds on new market data
