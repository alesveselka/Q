import datetime as dt
from enum import EventType
from enum import Interval
from enum import SignalType
from enum import OrderResultType
from enum import Study
from enum import Table
from position import Position
from report import Report
from order import Order


class Simulate:

    def __init__(self, timer, data_series, risk, account, broker, portfolio, trading_model):
        self.__timer = timer
        self.__data_series = data_series
        self.__risk = risk
        self.__account = account
        self.__broker = broker
        self.__portfolio = portfolio
        self.__trading_model = trading_model
        self.__trading_signals = []

        now = dt.datetime.now()
        # end_date = dt.date(now.year, now.month, now.day)
        # end_date = dt.date(1992, 6, 10)
        end_date = dt.date(1992, 12, 31)

        self.__data_series.load_and_calculate_data(end_date)
        self.__subscribe()

        self.__start(data_series.start_date(), end_date)

    def __subscribe(self):
        """
        Subscribe to listen timer's events
        """
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)
        self.__timer.on(EventType.EOD_DATA, self.__on_eod_data)

    def __start(self, start_date, end_date):
        """
        Start the simulation
        
        :param start_date:  start date fo the simulation
        :param end_date:    end date of the simulation
        """
        self.__timer.on(EventType.COMPLETE, self.__on_timer_complete)
        self.__timer.start(start_date, end_date)

    def __on_timer_complete(self, date):
        """
        Timer Complete event handler

        :param date:    date of the complete event
        """
        # Persist(
        #     self.__connection,
        #     self.__start_date,
        #     date,
        #     self.__broker.order_results(),
        #     self.__account,
        #     self.__portfolio,
        #     self.__futures,
        #     self.__study_parameters()
        # )

        start_date = self.__data_series.start_date()
        report = Report(self.__account)
        # print '\n'.join(report.transactions(start_date, date))
        print '\n'.join(report.to_lists(start_date, date, Interval.MONTHLY))
        # report.to_lists(start_date, date, Interval.MONTHLY)
        print '\n'.join(report.to_lists(start_date, date))

    def __on_market_open(self, date, previous_date):
        """
        Market Open event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        self.__transfer_orders(self.__orders(date))

        # TODO what if signals will be deleted on holiday and next day no orders created?
        del self.__trading_signals[:]

    def __on_market_close(self, date, previous_date):
        """
        Market Close event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        self.__broker.update_account(date, previous_date, self.__portfolio.open_positions())

    def __on_eod_data(self, date, previous_date):
        """
        End-of-Day event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        self.__trading_signals = self.__trading_model.signals(date, self.__portfolio.open_positions())

    def __transfer_orders(self, orders):
        """
        Transfer orders to broker

        :param orders:  list of order objects
        """
        for order in orders:
            order_result = self.__broker.transfer(order, self.__portfolio.open_positions())

            if order_result.type() == OrderResultType.FILLED:
                signal_type = order.signal_type()
                if signal_type == SignalType.ENTER:
                    self.__portfolio.add_position(Position(order_result))

                if signal_type == SignalType.ROLL_ENTER or signal_type == SignalType.ROLL_EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)

                if signal_type == SignalType.EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)
                    self.__portfolio.remove_position(position)

    def __orders(self, date):
        """
        Generate Orders from Signals

        :param date:    date for the market open
        """
        orders = []

        for signal in self.__trading_signals:
            market = signal.market()

            if market.has_data(date):
                market_data = market.data(end_date=date)
                atr_long = market.study(Study.ATR_LONG, date)[-1][Table.Study.VALUE]
                open_price = market_data[-1][Table.Market.OPEN_PRICE]
                enter_signals = [s for s in self.__trading_signals if s.type() == SignalType.ENTER]
                exit_signals = [s for s in self.__trading_signals if s.type() == SignalType.EXIT]
                roll_signals = [s for s in self.__trading_signals if s.type() == SignalType.ROLL_ENTER or s.type() == SignalType.ROLL_EXIT]
                market_position = self.__portfolio.market_position(market)

                if market_position and (signal in exit_signals or signal in roll_signals):
                    orders.append(Order(market, signal, date, open_price, market_position.quantity()))

                if market_position is None and signal in enter_signals:
                    quantity = self.__risk.position_size(market.point_value(), market.currency(), atr_long, date)
                    # TODO keep track of signal that don't pass
                    if quantity:
                        orders.append(Order(market, signal, date, open_price, quantity))

        return orders