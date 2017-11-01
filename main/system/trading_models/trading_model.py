#!/usr/bin/python

from abc import ABCMeta, abstractmethod


class TradingModel:
    """
    Abstract Base Class for all trading models
    """

    __metaclass__ = ABCMeta

    def __init__(self, name):
        """
        Initialize model with name
        
        :param string name: 
        """
        self._name = name

    def name(self):
        """
        Return model's name
        
        :return string: 
        """
        return self._name

    @abstractmethod
    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        raise NotImplementedError("Should implement 'signals()'")

    def _should_roll(self, date, previous_date, market, position_contract, signals):
        """
        Check if position should roll to the next contract
        
        :param date:                current date
        :param previous_date:       previous date
        :param market:              market of the position
        :param position_contract:   position contract
        :param signals:             signals
        :return:                    Boolean indicating if roll signals should be generated
        """
        should_roll = False

        if len([s for s in signals if s.market() == market]) == 0:
            contract = market.contract(date)
            should_roll = (contract != position_contract and contract != market.contract(previous_date)) \
                if position_contract else date.month != previous_date.month

        return should_roll

    def _position_contract(self, position_contract):
        """
        Return position contract if its not 'None', otherwise return NoneType
        
        :param string position_contract:    contract symbol
        :return:                            string representing the contract or NoneType
        """
        return position_contract if position_contract != 'None' else None
