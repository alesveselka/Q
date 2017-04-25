#!/usr/bin/python


class InvestmentUniverse(object):

    def __init__(self, name, connection):

        self.__name = name
        self.__connection = connection
        self.__start_contract_date = None
        self.__start_data_date = None
        self.__market_ids = []

    def start_contract_date(self):
        """
        Return date of first contract

        :return:    date
        """
        return self.__start_contract_date

    def start_data_date(self):
        """
        Return date of first data

        :return:    date
        """
        return self.__start_data_date

    def market_ids(self):
        """
        Return list of market IDs

        :return: list of integers
        """
        return self.__market_ids

    def load_data(self):
        """
        Load data
        """
        cursor = self.__connection.cursor()
        cursor.execute("""
            SELECT contract_start_date, data_start_date, market_ids
            FROM investment_universe
            WHERE name = '%s';
        """ % self.__name)
        data = cursor.fetchone()
        self.__start_contract_date = data[0]
        self.__start_data_date = data[1]
        self.__market_ids = data[2].split(',')
