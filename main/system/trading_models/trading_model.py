#!/usr/bin/python

from abc import ABCMeta, abstractmethod


class TradingModel:
    """
    Abstract Base Class for all trading models
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def signals(self, date, positions):
        """
        Generate trading signals

        :param date:            date for the market open
        :param positions:       list of open positions
        """
        raise NotImplementedError("Should implement 'signals()'")

    def _market_position(self, positions, market):
        """
        Find and return position by market passed in
        
        :param positions:   list of open positions
        :param market:      Market to filter by
        :return:            Position object
        """
        positions = [p for p in positions if p.market() == market]
        return positions[0] if len(positions) == 1 else None

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
