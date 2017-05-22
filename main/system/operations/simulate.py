from enum import EventType


class Simulation:  # TODO Refactor to operation 'Simulate'?

    # def __init__(self, timer, risk, portfolio, trading_model, params, studies, roll_strategy, investment_universe):
    def __init__(self, simulation_id, timer, risk, portfolio):
        self.__timer = timer
        self.__risk = risk
        self.__portfolio = portfolio
        self.__trading_model = trading_model
        self.__params = params
        self.__studies = studies
        self.__investment_universe = investment_universe

    def subscribe(self):
        """
        Subscribe to listen timer's events
        """
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)
        self.__timer.on(EventType.EOD_DATA, self.__on_eod_data)

    def start(self):
        pass

    def __on_market_open(self, date, previous_date):
        """
        Market Open event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        pass

    def __on_market_close(self, date, previous_date):
        """
        Market Close event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        pass

    def __on_eod_data(self, date, previous_date):
        """
        End-of-Day event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        pass
