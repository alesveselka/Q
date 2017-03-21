#!/usr/bin/python


class Portfolio(object):

    def __init__(self):
        self.__positions = []

    def add_position(self, position):
        self.__positions.append(position)

    def remove_position(self, position):
        self.__positions.remove(position)

    def positions_in_market(self, market):
        return [p for p in self.__positions if p.market() == market]

    def positions(self):
        return self.__positions
