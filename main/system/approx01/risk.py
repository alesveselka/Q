#!/usr/bin/python


class Risk(object):

    def __init__(self, position_sizing):
        self.__position_sizing = position_sizing

    def position_sizing(self):
        return self.__position_sizing
