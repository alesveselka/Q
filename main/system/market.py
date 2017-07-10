#!/usr/bin/python

import datetime as dt
from math import ceil
from enum import Study
from enum import Table
from enum import RollSchedule
from operator import itemgetter
from math import floor, log10
from collections import defaultdict
from collections import deque


class Market(object):  # TODO rename to Future?

    def __init__(self,
                 start_data_date,
                 market_id,
                 roll_strategy_id,
                 slippage_map,
                 name,
                 code,
                 data_codes,
                 currency,
                 first_data_date,
                 group,
                 tick_value,
                 point_value,
                 margin):

        self.__start_data_date = start_data_date
        self.__id = market_id
        self.__roll_strategy_id = roll_strategy_id
        self.__slippage_map = slippage_map
        self.__name = name
        self.__market_code = code
        self.__instrument_code = ''.join([code, '2']) if 'C' in data_codes else code
        self.__currency = currency
        self.__first_data_date = first_data_date
        self.__group = group
        self.__tick_value = tick_value
        self.__point_value = point_value
        self.__margin = margin
        self.__margin_multiple = 0.0
        self.__adjusted_data = []
        self.__data_indexes = {}
        self.__contracts = defaultdict(list)
        self.__contract_rolls = []
        self.__roll_schedule = []
        self.__scheduled_rolls = []
        self.__actual_rolls = []
        self.__studies = {}
        self.__study_indexes = {}
        self.__first_study_date = dt.date(9999, 12, 31)
        self.__has_study_data = False

        self.__dynamic_data = []
        self.__dynamic_indexes = {}
        self.__dynamic_studies = defaultdict(list)
        self.__dynamic_study_data = {}
        self.__dynamic_study_indexes = defaultdict(dict)

    def id(self):
        return self.__id

    def code(self):
        return self.__instrument_code

    def currency(self):
        return self.__currency

    def point_value(self):
        return self.__point_value

    def first_study_date(self):
        return self.__first_study_date

    def data(self, date):
        """
        Return market data at the date passed in

        :param date:    date of the required data
        :return:        tuple representing one day record
        """
        # index = self.__data_indexes[date] if date in self.__data_indexes else None
        # return (self.__adjusted_data[index], self.__adjusted_data[index-1]) if index else (None, None)
        index = self.__dynamic_indexes[date] if date in self.__dynamic_indexes else None
        return (self.__dynamic_data[index], self.__dynamic_data[index-1]) if index else (None, None)

    def data_range(self, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Return data between the start and end date passed in
        
        :param start_date:  start date of the data
        :param end_date:    end date of the data
        :return:            list of data
        """
        return [d for d in self.__dynamic_data if start_date <= d[Table.Market.PRICE_DATE] <= end_date]

    def margin(self, date):
        """
        Calculates margin estimate

        :param date:    Date on which to estimate the margin
        :return:        Number representing margin in account-base-currency
        """
        # return ceil(self.__margin_multiple * self.study(Study.ATR_SHORT, date)[Table.Study.VALUE])
        return ceil(self.data(date)[0][Table.Market.SETTLE_PRICE] * self.__point_value * 0.1)

    def slippage(self, date, quantity):
        """
        Calculates and returns 'slippage' in points
        (At minimum 1 tick)

        :param date:        date on which to calculate the slippage
        :param quantity:    number of contracts to open
        :return:            Number representing slippage in market points
        """
        atr = self.study(Study.ATR_SHORT, date)[Table.Study.VALUE]
        volume = self.study(Study.VOL_SHORT, date)[Table.Study.VALUE]
        atr_multiple = [s for s in self.__slippage_map if s['min'] <= volume < s['max']][0].get('atr')
        quantity_factor = 2 ** floor(log10(quantity))
        slippage_value = atr_multiple * atr
        result = (ceil(slippage_value / self.__tick_value) * self.__tick_value) / self.__point_value
        return result * quantity_factor

    def contract_roll(self, current_contract):
        """
        Find and return contract roll based on current contract passed in
        
        :param current_contract:    string representing current contract
        :return:                    tuple(date, gap, roll-out-contract, roll-in-contract)
        """
        rolls = self.__contract_rolls if len(self.__contract_rolls) else self.__scheduled_rolls
        return [r for r in rolls if r[Table.ContractRoll.ROLL_OUT_CONTRACT] == current_contract][0]

    def yield_curve(self, date):
        """
        Calculate yield curve relative to the date passed in
        
        :param date:    date to which relate the yield curve
        :return:        list of tuples(code, price, volume, yield, relative-price-difference))
        """
        current_contract_code = self.__contract(date)
        current_contract = [c for c in self.__contracts[current_contract_code] if c[Table.Market.PRICE_DATE] <= date][-1]
        contract_codes = [k for k in sorted(self.__contracts.keys()) if k > current_contract_code]
        previous_price = current_contract[Table.Market.SETTLE_PRICE] if current_contract else 0
        curve = [(
            current_contract_code,
            current_contract[Table.Market.SETTLE_PRICE],
            current_contract[Table.Market.VOLUME],
            None,
            None,
            (current_contract[Table.Market.LAST_TRADING_DAY] - date).days
        )]

        # TODO normalize with ATR
        # TODO also calculate average volatility of each contract
        for code in contract_codes:
            next_contract_data = [c for c in self.__contracts[code] if c[Table.Market.PRICE_DATE] <= date]
            if len(next_contract_data):
                next_contract = next_contract_data[-1]
                days = (next_contract[Table.Market.LAST_TRADING_DAY] - date).days
                price = next_contract[Table.Market.SETTLE_PRICE]
                implied_yield = (price / current_contract[Table.Market.SETTLE_PRICE]) ** (365. / days) - 1
                price_difference = price - previous_price
                previous_price = price
                curve.append((code, price, next_contract[Table.Market.VOLUME], implied_yield, price_difference, days))

        return curve

    def __contract(self, date):
        """
        Find and return contract to be in on the date passed in
        
        :param date:    date of the contract
        :return:        string representing the contract delivery
        """
        rolls = self.__contract_rolls if len(self.__contract_rolls) else self.__scheduled_rolls
        contract_rolls = [r for r in zip(rolls, rolls[1:]) if r[0][Table.ContractRoll.DATE] <= date < r[1][Table.ContractRoll.DATE]]
        contract_roll = contract_rolls[0][0] if len(contract_rolls) == 1 \
            else (rolls[0] if date < rolls[0][Table.ContractRoll.DATE] else rolls[-1])

        return contract_roll[Table.ContractRoll.ROLL_IN_CONTRACT]

    def study(self, study_name, date=None):
        """
        Return data of the study to the date passed in

        :param study_name:  Name of the study which data to return
        :param date:        last date of data required
        :return:            List of tuples - records of study specified
        """
        # index = (self.__study_indexes[study_name][date] if date in self.__study_indexes[study_name] else None) \
        #     if date else len(self.__study_indexes[study_name]) - 1
        # return self.__studies[study_name][index] if index > -1 else None
        index = (self.__dynamic_study_indexes[study_name][date] if date in self.__dynamic_study_indexes[study_name] else None) \
            if date else len(self.__dynamic_study_indexes[study_name]) - 1
        return self.__dynamic_studies[study_name][index] if index > -1 else None

    def study_range(self, study_name, start_date=dt.date(1900, 1, 1), end_date=dt.date(9999, 12, 31)):
        """
        Return study data within range of the dates passed in
        
        :param study_name:  name of the study to return
        :param start_date:  start date of the data range
        :param end_date:    end date of the data range
        :return:            list of tuple(date, value, value_2)
        """
        return [s for s in self.__studies[study_name] if start_date <= s[Table.Study.DATE] <= end_date]

    def calculate_studies(self, study_parameters):
        """
        Calculates and saves studies based on parameters passed in

        :param study_parameters:    List of dictionaries with parameters for each study to calculate
        """
        if len(self.__adjusted_data):
            for params in study_parameters:
                # print params
                self.__studies[params['name']] = params['study'](
                    [tuple(map(lambda c: d[c], params['columns'])) for d in self.__adjusted_data],
                    params['window']
                )

            # self.__studies['EMA_50'] = EMA([(d[Table.Market.PRICE_DATE], d[Table.Market.SETTLE_PRICE]) for d in self.__adjusted_data], 50)

            for k in self.__studies.keys():
                self.__study_indexes[k] = {i[1][Table.Study.DATE]: i[0] for i in enumerate(self.__studies[k])}

            self.__first_study_date = max([self.__studies[k][0][0] for k in self.__studies.keys()])

            # margin = self.__margin if self.__margin else self.__adjusted_data[-1][Table.Market.SETTLE_PRICE] * self.__point_value * 0.1
            margin = self.__adjusted_data[-1][Table.Market.SETTLE_PRICE] * self.__point_value * 0.1
            # self.__margin_multiple = margin / self.study(Study.ATR_SHORT)[Table.Study.VALUE]
            self.__margin_multiple = margin / self.__studies[Study.ATR_SHORT][-1][Table.Study.VALUE]

    def update_data(self, date, columns):
        """
        Update dynamic data and studies
        
        :param date:                date of the data update
        :param columns:             data columns to update
        """
        # TODO not necessary if all markets have data - filter universe based on first contract date
        # rolls = self.__contract_rolls if len(self.__contract_rolls) else self.__scheduled_rolls
        # TODO don't have to call every single time - just before rolling
        contract = self.__contract(date) if len(self.__scheduled_rolls) else None
        contract_data = self.__contracts[contract] if contract else []
        # TODO cache contract data
        contract_data = [d for d in contract_data if d[Table.Market.PRICE_DATE] == date]
        if len(contract_data):
            # TODO also use 'deque' for data? -> probably won't need more during backtest. What about persisting?
            column_data = [(contract_data[-1][c]) for c in columns] if columns else contract_data[-1]
            if date in self.__dynamic_indexes:
                index = self.__dynamic_indexes[date]
                self.__dynamic_data[index] = column_data

                if self.__dynamic_data[index][Table.Market.CODE] != self.__dynamic_data[index-1][Table.Market.CODE]:
                    previous_contract = self.__contracts[self.__dynamic_data[index-1][Table.Market.CODE][-5:]]
                    previous_data = [d for d in previous_contract if d[Table.Market.PRICE_DATE] <= date][-1]
                    gap = self.__dynamic_data[index][Table.Market.SETTLE_PRICE] - previous_data[Table.Market.SETTLE_PRICE]
                    self.__actual_rolls.append((date, gap, self.__dynamic_data[index-1][Table.Market.CODE], self.__dynamic_data[index][Table.Market.CODE]))

                if len(self.__actual_rolls):
                    gap = sum(roll[1] for roll in self.__actual_rolls)
                    self.__dynamic_data[index] = (
                        column_data[Table.Market.CODE],
                        column_data[Table.Market.PRICE_DATE],
                        column_data[Table.Market.OPEN_PRICE] - gap,
                        column_data[Table.Market.HIGH_PRICE] - gap,
                        column_data[Table.Market.LOW_PRICE] - gap,
                        column_data[Table.Market.SETTLE_PRICE] - gap,
                        column_data[Table.Market.VOLUME],
                        column_data[Table.Market.LAST_TRADING_DAY]
                    )

            else:
                self.__dynamic_data.append(column_data)
                index = len(self.__dynamic_data) - 1
                self.__dynamic_indexes[date] = index

                if len(self.__actual_rolls):
                    gap = sum(roll[1] for roll in self.__actual_rolls)
                    self.__dynamic_data[index] = (
                        column_data[Table.Market.CODE],
                        column_data[Table.Market.PRICE_DATE],
                        column_data[Table.Market.OPEN_PRICE] - gap
                    )

    def update_studies(self, date, study_parameters):
        # if date in self.__data_indexes:
        if date in self.__dynamic_indexes:
            index = self.__dynamic_indexes[date]
            market_data = self.__dynamic_data[index]
            high = market_data[Table.Market.HIGH_PRICE]
            low = market_data[Table.Market.LOW_PRICE]
            settle = market_data[Table.Market.SETTLE_PRICE]
            previous_settle = self.__dynamic_data[index-1][Table.Market.SETTLE_PRICE] if index else settle
            volume = market_data[Table.Market.VOLUME]
            tr = max(high, previous_settle) - min(low, previous_settle)
            for window in set([params['window'] for params in study_parameters]):
                key = 'settle_price_%s' % window
                if key not in self.__dynamic_study_data: self.__dynamic_study_data[key] = deque([], window)
                self.__dynamic_study_data[key].append(settle)
                key = 'volume_%s' % window
                if key not in self.__dynamic_study_data: self.__dynamic_study_data[key] = deque([], window)
                self.__dynamic_study_data[key].append(volume)
                key = 'tr_%s' % window
                if key not in self.__dynamic_study_data: self.__dynamic_study_data[key] = deque([], window)
                self.__dynamic_study_data[key].append(tr)

            has_study = []
            for params in study_parameters:
                window = params['window']
                study_type = params['study']
                study_name = params['name']
                study = self.__dynamic_studies[study_name]
                data_columns = params['columns'][1:]
                study_data = self.__dynamic_study_data['%s_%s' % (data_columns[-1], window)] \
                    if len(data_columns) == 1 \
                    else self.__dynamic_study_data['tr_%s' % window]

                if study_type == 'SMA':
                    study.append((date, sum(study_data) / len(study_data)))

                if study_type == 'EMA':
                    c = 2.0 / (window + 1)
                    ma = (date, study[-1][1] if len(study) else (sum(study_data) / len(study_data)))
                    study.append((date, (c * settle) + (1 - c) * ma[1]))

                if study_type == 'ATR':  # Moving average TR
                    c = 2.0 / (window + 1)
                    ma = (date, study[-1][1] if len(study) else (sum(study_data) / len(study_data)))
                    study.append((date, (c * tr) + (1 - c) * ma[1]))

                if study_type == 'HHLL':  # Moving average max/min
                    study.append((date, max(study_data), min(study_data)))
                    # print 'HHLL', date, max(study_data), min(study_data)

                self.__dynamic_study_indexes[study_name][date] = len(study) - 1

                has_study.append(len(study) >= window)

            self.__has_study_data = all(has_study)

    def has_study_data(self):
        """
        Returns flag indicating if the market has studies data
        
        :return:    boolean
        """
        return self.__has_study_data

    def __should_roll(self, date, previous_date, market, position, signals):
        """
        Check if position should roll to the next contract
        
        :param date:            current date
        :param previous_date:   previous date
        :param market:          market of the position
        :param position:        position to roll
        :param signals:         signals
        :return:                Boolean indicating if roll signals should be generated
        """
        should_roll = False

        # contract_roll = market.contract_roll(position_contract)
        # roll_date = market.data(contract_roll[Table.ContractRoll.DATE])[-2][Table.Market.PRICE_DATE]
        # should_roll = date == roll_date and position_contract == contract_roll[Table.ContractRoll.ROLL_OUT_CONTRACT]

        return should_roll

    def load_data(self, connection, end_date, delivery_months):
        """
        Load market's data

        :param connection:      MySQLdb connection instance
        :param end_date:        Last date to fetch data to
        :param delivery_months: list of delivery months [(code, short-month-name)]
        """
        cursor = connection.cursor()
        continuous_query = """
            SELECT %s
            FROM %s
            WHERE market_id = '%s'
            AND code = '%s'
            AND roll_strategy_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
        cursor.execute(continuous_query % (
            self.__column_names(),
            'continuous_adjusted',
            self.__id,
            self.__instrument_code,
            2,  #self.__roll_strategy_id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        # TODO I can make a generator and retrieve the data when needed
        self.__adjusted_data = cursor.fetchall()
        self.__data_indexes = {i[1][Table.Market.PRICE_DATE]: i[0] for i in enumerate(self.__adjusted_data)}

        contracts_query = """
            SELECT %s
            FROM %s
            WHERE market_id = '%s'
            AND DATE(price_date) >= '%s'
            AND DATE(price_date) <= '%s'
            ORDER BY price_date;
        """
        cursor.execute(contracts_query % (
            self.__column_names() + ', last_trading_day',
            'contract',
            self.__id,
            self.__start_data_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ))
        # TODO need to load more than 'end_date' - for the last contract to roll out and in contracts
        for c in cursor.fetchall():
            self.__contracts[c[Table.Market.CODE][-5:].upper()].append(c)
        #
        # contract_roll_query = """
        #     SELECT date, gap, roll_out_contract, roll_in_contract
        #     FROM contract_roll
        #     WHERE market_id = '%s'
        #     AND roll_strategy_id = '%s'
        #     ORDER BY date;
        # """
        # cursor.execute(contract_roll_query % (self.__id, self.__roll_strategy_id))
        # self.__contract_rolls = cursor.fetchall()
        #
        roll_schedule_query = """
            SELECT roll_out_month, roll_in_month, month, day
            FROM standard_roll_schedule
            WHERE market_id = '%s'
            AND name = 'norgate';
        """
        cursor.execute(roll_schedule_query % self.__id)
        self.__roll_schedule = cursor.fetchall()

        contract_codes = self.__scheduled_codes([k for k in sorted(self.__contracts.keys())], delivery_months)
        self.__scheduled_rolls = [(self.__scheduled_roll_date(r[0], delivery_months), 0, r[0], r[1])
                                  for r in zip(contract_codes, contract_codes[1:])]

        # for roll in self.__scheduled_rolls:
        #     print roll

        return True

    def __scheduled_codes(self, contract_codes, delivery_months):
        """
        Filter out contract codes which months are not included in scheduled rolls
        
        :param contract_codes:  list of contract codes
        :param delivery_months: list of delivery months [(code, short-month-name)]
        :return:                list of contract codes
        """
        scheduled_months = [r[RollSchedule.ROLL_OUT_MONTH] for r in self.__roll_schedule]
        scheduled_codes = [k for k in delivery_months.keys() if delivery_months[k][1] in scheduled_months]
        return [c for c in contract_codes if c[-1] in scheduled_codes]

    def __scheduled_roll_date(self, contract, delivery_months):
        """
        Return market's next scheduled roll date based on contract passed in
        
        :param contract:        contract which roll date to find
        :param delivery_months: list of delivery months [(code, short-month-name)]
        :return:                date of scheduled roll
        """
        # months = [m for m in calendar.month_abbr]

        contract_year = int(contract[:4])
        contract_month_code = contract[-1]
        # contract_month_index = reduce(lambda i, d: i + 1 if d[0] <= contract_month_code else i, delivery_months, 0)
        contract_month_index = delivery_months[contract_month_code][0]
        contract_month = delivery_months[contract_month_code][1]
        # contract_month = months[contract_month_index]

        roll_schedule = [r for r in self.__roll_schedule if r[RollSchedule.ROLL_OUT_MONTH] == contract_month][0]

        # roll_month_index = [i[0] for i in enumerate(months) if i[1] == roll_schedule[RollSchedule.MONTH]][0]
        roll_month_index = [delivery_months[k][0] for k in delivery_months.keys() if delivery_months[k][1] == roll_schedule[RollSchedule.MONTH]][0]
        roll_year = contract_year if contract_month_index - roll_month_index > -1 else contract_year - 1
        return dt.date(roll_year, roll_month_index, int(roll_schedule[RollSchedule.DAY]))

    def __column_names(self):
        """
        Construct and return column names sorted by their index in ENUM

        :return:    string
        """
        # TODO External 'Entity'?
        columns = {
            'code': Table.Market.CODE,
            'price_date': Table.Market.PRICE_DATE,
            'open_price': Table.Market.OPEN_PRICE,
            'high_price': Table.Market.HIGH_PRICE,
            'low_price': Table.Market.LOW_PRICE,
            'settle_price': Table.Market.SETTLE_PRICE,
            'volume': Table.Market.VOLUME
        }
        return ', '.join([i[0] for i in sorted(columns.items(), key=itemgetter(1))])
