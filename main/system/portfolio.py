#!/usr/bin/python


class Portfolio(object):

    def __init__(self, account):
        self.__account = account
        self.__positions = []
        self.__closed_positions = []

    def add_position(self, position):
        self.__positions.append(position)

    def remove_position(self, position):
        self.__closed_positions.append(position)
        self.__positions.remove(position)

    def market_position(self, market):
        positions = [p for p in self.__positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None

    def open_positions(self):
        return self.__positions

    def closed_positions(self):
        return self.__closed_positions
