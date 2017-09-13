#!/usr/bin/python

import datetime as dt
from enum import EventType
from enum import Interval
from enum import Direction
from enum import SignalType
from enum import OrderType
from enum import OrderResultType
from enum import Study
from enum import Table
from position import Position
from report import Report
from order import Order
from timer import Timer
from strategy_signal import Signal
from order_result import OrderResult
from persist import Persist


class Simulate:

    def __init__(self, simulation, roll_strategy, data_series, risk, account, broker, portfolio, trading_model):
        self.__simulation = simulation
        self.__roll_strategy = roll_strategy
        self.__data_series = data_series
        self.__risk = risk
        self.__account = account
        self.__broker = broker
        self.__portfolio = portfolio
        self.__trading_model = trading_model
        self.__trading_signals = []
        self.__order_results = []
        self.__timer = Timer()

        now = dt.datetime.now()
        # end_date = dt.date(now.year, now.month, now.day)
        # end_date = dt.date(1992, 6, 10)
        end_date = dt.date(1992, 5, 31)

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
            self.__order_results,
            self.__account,
            self.__portfolio,
            self.__data_series
        )

        # f = open('2_report_full_1993-12-31.txt', 'w')
        # f.write(full_report)
        # f.close()
        #
        # f = open('2_report_yearly_1993-12-31.txt', 'w')
        # f.write('\n'.join(report.to_lists(start_date, date, Interval.YEARLY)))
        # f.close()
        #
        # f = open('2_transactions_1993-12-31.txt', 'w')
        # f.write('\n'.join(report.transactions(start_date, date)))
        # f.close()

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

        self.__transfer_orders(self.__orders(date))

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

        self.__broker.update_account(date, previous_date, self.__portfolio.open_positions())

        self.__trading_signals += self.__trading_model.signals(date, self.__portfolio.open_positions())

    def __transfer_orders(self, orders):
        """
        Transfer orders to broker

        :param orders:  list of order objects
        """
        for order in orders:
            order_result = order.quantity() \
                           and self.__broker.transfer(order, self.__portfolio.open_positions()) \
                           or OrderResult(OrderResultType.REJECTED, order, 0, 0, 0, 0)
            result_type = order_result.type()

            # TODO keep 'PARTIALLY_FILLED' signal to try fill rest next day?
            if result_type == OrderResultType.FILLED or result_type == OrderResultType.PARTIALLY_FILLED:
                signal_type = order.signal_type()
                if signal_type == SignalType.ENTER:
                    self.__portfolio.add_position(Position(order_result))

                if signal_type == SignalType.REBALANCE:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)
                    # self.__portfolio.update_position(position, Position(order_result))

                if signal_type == SignalType.ROLL_ENTER or signal_type == SignalType.ROLL_EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)

                if signal_type == SignalType.EXIT:
                    position = self.__portfolio.market_position(order.market())
                    position.add_order_result(order_result)
                    self.__portfolio.remove_position(position)

            self.__order_results.append(order_result)

    def __orders(self, date):
        """
        Generate Orders from Signals

        :param date:    date for the market open
        """
        orders = []
        signals_to_remove = []
        enter_signals = [s for s in self.__trading_signals if s.type() == SignalType.ENTER]
        exit_signals = [s for s in self.__trading_signals if s.type() == SignalType.EXIT]
        roll_signals = [s for s in self.__trading_signals if s.type() == SignalType.ROLL_ENTER or s.type() == SignalType.ROLL_EXIT]

        open_markets = sorted([p.market() for p in self.__portfolio.open_positions()])
        markets_to_close = sorted([s.market() for s in exit_signals])
        markets_to_open = sorted([s.market() for s in enter_signals])
        markets_to_roll = sorted(set([s.market() for s in roll_signals]))
        candidate_markets = set(open_markets).difference(markets_to_close).union(markets_to_open)
        open_ids = [market.id() for market in open_markets]
        ids_to_close = [market.id() for market in markets_to_close]
        ids_to_open = [market.id() for market in markets_to_open]
        ids_to_roll = [market.id() for market in markets_to_roll]
        candidate_ids = [market.id() for market in candidate_markets]

        position_inertia = 0.1

        print date, '*' * 50

        print 'open', open_ids
        print 'new', sorted(candidate_ids)
        print 'close', sorted(ids_to_close)
        print 'rebalance', sorted(set(open_ids).difference(ids_to_close).difference(ids_to_roll))
        print 'roll', sorted(ids_to_roll)

        # TODO 'position_sizes' doesn't have to return all candidate markets due contract size -- mark as rejected
        position_sizes = self.__risk.position_sizes(date, candidate_markets)

        # for market_id in set(position_sizes.keys()).union(ids_to_close):
        #     open_position_size = [p.quantity() for p in self.__portfolio.open_positions() if p.market().id() == market_id]
        #     current_size = open_position_size[0] if len(open_position_size) else 0
        #     position_size = position_sizes[market_id] if market_id in position_sizes else 0.0
        #     diff = ((position_size - current_size) / current_size) if current_size else 1.0
        #     print market_id, current_size, position_size, round(diff, 2)

        print 'position_sizes', position_sizes

        for signal in exit_signals:
            market = signal.market()
            market_data, previous_data = market.data(date)
            if market_data:
                open_price = market_data[Table.Market.OPEN_PRICE]
                market_position = self.__portfolio.market_position(market)
                if market_position:
                    # orders.append(Order(market, signal, date, open_price, market_position.quantity(), market_position.contract()))
                    print 'EXIT', market.id(), market.code(), market_position.contract(), market_position.quantity()

        for signal in enter_signals:
            market = signal.market()
            market_data, previous_data = market.data(date)
            if market_data:
                open_price = market_data[Table.Market.OPEN_PRICE]
                market_position = self.__portfolio.market_position(market)
                if market_position is None:
                    # orders.append(Order(market, signal, date, open_price, position_sizes[market.id()], market.contract(date)))
                    print 'ENTER', market.id(), market.code(), market.contract(date), position_sizes[market.id()]

        for market in set(open_markets).difference(markets_to_close).difference(markets_to_roll):
            market_data, previous_data = market.data(date)
            if market_data:
                open_price = market_data[Table.Market.OPEN_PRICE]
                market_position = self.__portfolio.market_position(market)
                if market_position:
                    quantity = float(market_position.quantity())
                    position_size = position_sizes[market.id()]
                    diff = position_size - quantity
                    direction = market_position.direction()
                    order_type = self.__order_type(SignalType.REBALANCE, direction, diff)

                    self.__trading_signals.append(Signal(market, SignalType.REBALANCE, direction, date, open_price))

                    # orders.append(Order(market, signal, date, open_price, position_sizes[market.id()], market_position.contract()))
                    print 'REBALANCE', market.id(), market.code(), quantity, position_sizes[market.id()], diff, round(diff / quantity, 2), order_type

        for s in roll_signals:
            market = s.market()
            market_data, previous_data = market.data(date)
            if market_data:
                open_price = market_data[Table.Market.OPEN_PRICE]
                market_position = self.__portfolio.market_position(market)
                if market_position:
                    if s.type() == SignalType.ROLL_EXIT:
                        # orders.append(Order(market, signal, date, open_price, market_position.quantity(), market_position.contract()))
                        print 'ROLL EXIT', market.id(), market.code(), market_position.contract(), market_position.quantity()
                    elif s.type() == SignalType.ROLL_ENTER:
                        # orders.append(Order(market, signal, date, open_price, position_sizes[market.id()], market.contract(date)))
                        print 'ROLL ENTER', market.id(), market.code(), market.contract(date), position_sizes[market.id()]



        for signal in self.__trading_signals:
            market = signal.market()
            market_data, previous_data = market.data(date)

            if market_data:
                # atr_long = market.study(Study.ATR_LONG, previous_data[Table.Market.PRICE_DATE])[Table.Study.VALUE]
                open_price = market_data[Table.Market.OPEN_PRICE]
                position = self.__portfolio.market_position(market)
                signal_type = signal.type()
                order_type = self.__order_type(signal.type(), signal.direction())

                if position and signal in exit_signals:
                    orders.append(Order(market, order_type, signal_type, date, open_price, position.quantity(), position.contract()))

                if position and signal in roll_signals:
                    # contract = market.contract(date) if signal.type() == SignalType.ROLL_ENTER else position.contract()
                    # orders.append(Order(market, order_type, signal_type, date, open_price, position.quantity(), contract))
                    if signal.type() == SignalType.ROLL_EXIT:
                        orders.append(Order(market, order_type, signal_type, date, open_price, position.quantity(), position.contract()))
                    elif signal.type() == SignalType.ROLL_ENTER:
                        orders.append(Order(market, order_type, signal_type, date, open_price, position_sizes[market.id()], market.contract(date)))

                if position and signal_type == SignalType.REBALANCE:
                    quantity = abs(position_sizes[market.id()] - position.quantity())
                    # TODO position inertia
                    if quantity:
                        print 'Rebalance quantity', quantity, market.id(), market.code()
                        orders.append(Order(market, order_type, signal_type, date, open_price, quantity, position.contract()))

                if position is None and signal in enter_signals:
                    # TODO don't calculate Qty -- it will be calculated with relations to open positions as well.
                    # quantity = self.__risk.position_size(market.point_value(), market.currency(), atr_long, date)
                    orders.append(Order(market, order_type, signal_type, date, open_price, position_sizes[market.id()], market.contract(date)))

                signals_to_remove.append(signal)

        for signal in signals_to_remove:
            self.__trading_signals.remove(signal)

        return orders

    def __order_type(self, signal_type, direction, position_difference=0.0):
        """
        Determine order type based on signal type, direction and optionally position difference
        
        :param signal_type:         type of signal
        :param direction:           direction of position
        :param position_difference: difference between current position size and new one, in case of rebalance signal
        :return: 
        """
        return {
            SignalType.ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.EXIT: {Direction.LONG: OrderType.STC, Direction.SHORT: OrderType.BTC},
            SignalType.ROLL_ENTER: {Direction.LONG: OrderType.BTO, Direction.SHORT: OrderType.STO},
            SignalType.ROLL_EXIT: {Direction.LONG: OrderType.STC, Direction.SHORT: OrderType.BTC},
            SignalType.REBALANCE: {
                Direction.LONG: OrderType.BTO if position_difference >= 0 else OrderType.STC,
                Direction.SHORT: OrderType.STO if position_difference >= 0 else OrderType.BTC
            }
        }.get(signal_type).get(direction)
