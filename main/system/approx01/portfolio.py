#!/usr/bin/python


class Portfolio(object):

    def __init__(self):
        self.__positions = []

    def add_position(self, position):
        self.__positions.append(position)

    def has_position(self):
        return True
