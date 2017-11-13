#!/usr/bin/python

import datetime as dt
from enum import EventType
from enum import Interval
from enum import OrderResultType
from enum import Table
from enum import Study
from report import Report
from order import Order
from timer import Timer
from order_result import OrderResult
from persist import Persist


class Simulate:

    def __init__(self,
                 simulation,
                 roll_strategy,
                 data_series,
                 risk,
                 account,
                 broker,
                 trading_model,
                 position_inertia,
                 use_position_inertia):
        self.__simulation = simulation
        self.__roll_strategy = roll_strategy
        self.__data_series = data_series
        self.__risk = risk
        self.__account = account
        self.__broker = broker
        self.__trading_model = trading_model
        self.__position_inertia = position_inertia
        self.__use_position_inertia = use_position_inertia
        self.__trading_signals = []
        self.__position_sizes = {}
        self.__timer = Timer()

        end_date = dt.date(1992, 12, 31)

        self.__data_series.load(end_date, roll_strategy[Table.RollStrategy.ID])
        self.__subscribe()

        self.__start(data_series.start_date(), end_date)

    def __subscribe(self):
        """
        Subscribe to listen timer's events
        """
        self.__timer.on(EventType.MARKET_OPEN, self.__on_market_open)
        # self.__timer.on(EventType.MARKET_CLOSE, self.__on_market_close)
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
        start_date = self.__data_series.start_date()
        report = Report(self.__account)
        # print '\n'.join(report.transactions(start_date, date))
        # print '\n'.join(report.to_lists(start_date, date, Interval.YEARLY))
        # report.to_lists(start_date, date, Interval.MONTHLY)
        # print '\n'.join(report.to_lists(start_date, date))
        full_report = '\n'.join(report.to_lists(start_date, date))

        print full_report

        Persist(
            self.__simulation[Table.Simulation.ID],
            self.__roll_strategy,
            start_date,
            date,
            self.__account,
            self.__broker,
            self.__data_series
        )

        # self.__log(report, full_report, start_date, date, Interval.MONTHLY)

    def __on_market_open(self, date, previous_date):
        """
        Market Open event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # Update all data (Open, High, Low, Settle, ...) although only 'open' price is available now.
        # The reason is to enclose slipped price in high - low range when executed on open,
        # and also for simpler and faster calculations
        self.__data_series.update_futures_data(date)

        open_positions = self.__broker.positions(previous_date)
        self.__transfer_orders(self.__orders(date, open_positions), open_positions)

    def __on_market_close(self, date, previous_date):
        """
        Market Close event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        # self.__broker.update_account(date, previous_date, self.__portfolio.open_positions())

    def __on_eod_data(self, date, previous_date):
        """
        End-of-Day event handler

        :param date:            date for the market open
        :param previous_date:   previous market date
        """
        self.__data_series.update_futures_studies(date)

        # Account update
        self.__broker.update_account(date, previous_date)
        open_positions = self.__broker.positions(date)

        # Trading signals and position sizing
        self.__trading_signals += self.__trading_model.signals(date, open_positions)
        markets = {s.market().id(): s.market() for s in self.__trading_signals}
        forecasts = {'%s_%s' % (s.market().id(), s.contract()): s.forecast() for s in self.__trading_signals}
        self.__position_sizes = self.__risk.position_sizes(date, markets, forecasts)

    def __transfer_orders(self, orders, open_positions):
        """
        Transfer orders to broker

        :param orders:  list of order objects
        """
        for order in orders:
            key = '%s_%s' % (order.market().id(), order.contract())
            position_size = self.__position_sizes[key]
            open_position = open_positions[key] if key in open_positions else 0
            order_result = order.quantity() \
                           and self.__broker.transfer(order, position_size, open_position) \
                           or OrderResult(OrderResultType.REJECTED, order, 0, 0, 0, 0)
            # TODO check remaining partially-filled orders

    def __orders(self, date, open_positions):
        """
        Generate Orders from Signals

        :param date:            date for the market open
        :param open_positions:   previous market date
        """
        orders = []
        signals_to_remove = []

        for signal in self.__trading_signals:
            market = signal.market()
            market_data, previous_data = market.data(date)

            if market_data:
                key = '%s_%s' % (market.id(), signal.contract())
                open_position = open_positions[key] if key in open_positions else None
                position_size = self.__position_sizes[key]
                volume = market.study(Study.VOL_SHORT)[Table.Study.VALUE]
                sign = 1 if position_size >= 0 else -1
                liquid_position_size = position_size if abs(position_size) <= volume else int(volume / 3 * sign)
                if open_position is None or open_position != liquid_position_size:
                    order_size = liquid_position_size - (open_position if open_position else 0)
                    open_price = market_data[Table.Market.OPEN_PRICE]
                    no_trade_size = abs(open_position * self.__position_inertia if open_position else 0)
                    if abs(order_size) > no_trade_size:
                        orders.append(Order(date, market, signal.contract(), open_price, order_size))

                signals_to_remove.append(signal)

        for signal in signals_to_remove:
            self.__trading_signals.remove(signal)

        return orders

    def __log(self, report, full_report, start_date, end_date, interval):
        """
        Write down various reports into files
        
        :param Report report:       Report object
        :param string full_report:  summary report for whole simulation
        :param date start_date:     date of simulation start
        :param date end_date:       date of simulation end
        :param string interval:     interval sampling for reports
        """
        model_name = self.__trading_model.name()
        f = open('report_full_%s_%s.txt' % (end_date, model_name), 'w')
        f.write(full_report)
        f.close()

        f = open('report_%s_%s_%s.txt' % (interval.lower(), end_date, model_name), 'w')
        f.write('\n'.join(report.to_lists(start_date, end_date, interval)))
        f.close()

        f = open('transactions_%s_%s.txt' % (end_date, model_name), 'w')
        f.write('\n'.join(report.transactions(start_date, end_date)))
        f.close()
