#!/usr/bin/python

from abc import ABCMeta
from enum import Table
from enum import Interval
from datetime import timedelta


class BinaryTradingModel:
    """
    Abstract Base Class for binary (with explicit 'Enter' and 'Exit' signals) trading models
    """

    __metaclass__ = ABCMeta

    def __init__(self, rebalance_interval, roll_lookout_days):
        self._rebalance_interval = rebalance_interval
        self._roll_lookout_days = int(roll_lookout_days)

    def _should_rebalance(self, market, position_contract, date, previous_date, signals):
        """
        Check if position should be rebalanced based on data passed in
        
        :param Market market:               market for which to check the rebalance
        :param string position_contract:    contract for which to check the rebalnce
        :param date date:                   current date
        :param date previous_date:          previous date
        :param list signals:                list of new Signal objects
        :return boolean: 
        """
        rebalance = False
        if position_contract is not None and self._rebalance_interval == Interval.MONTHLY and date.month != previous_date.month:
            if not len([s for s in signals if s.market() == market and s.contract() == position_contract]):
                roll_date = date + timedelta(days=self._roll_lookout_days)
                scheduled_roll = market.scheduled_roll(roll_date)
                scheduled_contract = scheduled_roll[Table.ContractRoll.ROLL_IN_CONTRACT] if scheduled_roll else None
                rebalance = position_contract == scheduled_contract
        return rebalance
