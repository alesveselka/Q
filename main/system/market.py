#!/usr/bin/python

import calendar
import datetime as dt
from math import ceil
from enum import Study
from enum import Table
from enum import RollSchedule
from operator import itemgetter
from math import floor, log10
from collections import defaultdict
from collections import deque
from study import EMA


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
        self.__studies = {}
        self.__study_indexes = {}
        self.__first_study_date = dt.date(9999, 12, 31)

        self.__dynamic_data = []
        self.__dynamic_indexes = {}
        self.__dynamic_studies = defaultdict(list)
        self.__dynamic_study_data = {
            '50': deque([], 50),
            'tr_50': deque([], 51),
            'vol_50': deque([], 50),
            '100': deque([], 100),
            'tr_100': deque([], 101),
            'vol_100': deque([], 100)
        }
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
        index = self.__data_indexes[date] if date in self.__data_indexes else None
        return (self.__adjusted_data[index], self.__adjusted_data[index-1]) if index else (None, None)
        # index = self.__dynamic_indexes[date] if date in self.__dynamic_indexes else None
        # return (self.__dynamic_data[index], self.__dynamic_data[index-1]) if index else (None, None)

    def margin(self, date):
        """
        Calculates margin estimate

        :param date:    Date on which to estimate the margin
        :return:        Number representing margin in account-base-currency
        """
        return ceil(self.__margin_multiple * self.study(Study.ATR_SHORT, date)[Table.Study.VALUE])

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
        index = (self.__study_indexes[study_name][date] if date in self.__study_indexes[study_name] else None) \
            if date else len(self.__study_indexes[study_name]) - 1
        return self.__studies[study_name][index] if index > -1 else None
        # index = (self.__dynamic_study_indexes[study_name][date] if date in self.__dynamic_study_indexes[study_name] else None) \
        #     if date else len(self.__dynamic_study_indexes[study_name]) - 1
        # return self.__dynamic_studies[study_name][index] if index > -1 else None

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
                self.__studies[params['name']] = params['study'](
                    [tuple(map(lambda c: d[c], params['columns'])) for d in self.__adjusted_data],
                    params['window']
                )

            # self.__studies['EMA_50'] = EMA([(d[Table.Market.PRICE_DATE], d[Table.Market.SETTLE_PRICE]) for d in self.__adjusted_data], 50)

            for k in self.__studies.keys():
                self.__study_indexes[k] = {i[1][Table.Study.DATE]: i[0] for i in enumerate(self.__studies[k])}

            self.__first_study_date = max([self.__studies[k][0][0] for k in self.__studies.keys()])

            margin = self.__margin if self.__margin else self.__adjusted_data[-1][Table.Market.SETTLE_PRICE] * self.__point_value * 0.1
            # self.__margin_multiple = margin / self.study(Study.ATR_SHORT)[Table.Study.VALUE]
            self.__margin_multiple = margin / self.__studies[Study.ATR_SHORT][-1][Table.Study.VALUE]

    def update_data(self, date):
        """
        Update dynamic data and studies
        
        :param date:    date of the data update
        """
        # TODO not necessary if all markets have data - filter universe based on first contract date
        rolls = self.__contract_rolls if len(self.__contract_rolls) else self.__scheduled_rolls
        contract = self.__contract(date) if len(rolls) else None
        contract_data = self.__contracts[contract] if contract else []
        # TODO cache contract data
        contract_data = [d for d in contract_data if d[Table.Market.PRICE_DATE] == date]
        if len(contract_data):
            # TODO adjust for gap! And save the gap!
            self.__dynamic_data.append(contract_data[-1])
            self.__dynamic_indexes[date] = len(self.__dynamic_data) - 1

            # self.__update_studies(date, contract_data[-1])
            if date in self.__data_indexes:  # TODO this is only temporary, because some continuous and individual contract start on different date
                self.__update_studies(date)

    def __update_studies(self, date):
        short_window = 50
        long_window = 100
        index = self.__data_indexes[date]
        settle = self.__adjusted_data[index][Table.Market.SETTLE_PRICE]
        volume = self.__adjusted_data[index][Table.Market.VOLUME]
        tr = 0.0
        self.__dynamic_study_data['50'].append(settle)
        self.__dynamic_study_data['vol_50'].append(volume)
        if len(self.__dynamic_study_data['50']):
            tr = max(self.__adjusted_data[index][Table.Market.HIGH_PRICE], self.__adjusted_data[index-1][Table.Market.SETTLE_PRICE]) - \
                 min(self.__adjusted_data[index][Table.Market.LOW_PRICE], self.__adjusted_data[index-1][Table.Market.SETTLE_PRICE])
            self.__dynamic_study_data['tr_50'].append(tr)
        self.__dynamic_study_data['100'].append(settle)
        self.__dynamic_study_data['vol_100'].append(volume)
        if len(self.__dynamic_study_data['100']):
            self.__dynamic_study_data['tr_100'].append(tr)

        # SMA
        ma_short = self.__dynamic_studies[Study.MA_SHORT]
        ma_short.append((date, sum(self.__dynamic_study_data['50']) / len(self.__dynamic_study_data['50'])))
        self.__dynamic_study_indexes[Study.MA_SHORT][date] = len(ma_short) - 1

        ma_long = self.__dynamic_studies[Study.MA_LONG]
        ma_long.append((date, sum(self.__dynamic_study_data['100']) / len(self.__dynamic_study_data['100'])))
        self.__dynamic_study_indexes[Study.MA_LONG][date] = len(ma_long) - 1

        # EMA
        if len(self.__dynamic_study_data['50']) == short_window:
            ema_short = self.__dynamic_studies['EMA_50']
            c = 2.0 / (short_window + 1)
            ma = (date, ema_short[-1][1] if len(ema_short) else (sum(self.__dynamic_study_data['50']) / len(self.__dynamic_study_data['50'])))
            ema_short.append((date, (c * settle) + (1 - c) * ma[1]))

        # ATR
        atr_short = self.__dynamic_studies[Study.ATR_SHORT]
        if len(self.__dynamic_study_data['tr_50']) == short_window + 1:
            # EMA of TR
            c = 2.0 / (short_window + 1)
            # Slice the window to 50, so its same as original
            ma = (date, atr_short[-1][1] if len(atr_short) else (sum([tr for tr in self.__dynamic_study_data['tr_50']][1:]) / (len(self.__dynamic_study_data['tr_50'])-1)))
            atr_short.append((date, (c * self.__dynamic_study_data['tr_50'][-1]) + (1 - c) * ma[1]))
            self.__dynamic_study_indexes[Study.ATR_SHORT][date] = len(atr_short) - 1

        atr_long = self.__dynamic_studies[Study.ATR_LONG]
        if len(self.__dynamic_study_data['tr_100']) == long_window + 1:
            # EMA of TR
            c = 2.0 / (long_window + 1)
            # Slice the window to 50, so its same as original
            ma = (date, atr_long[-1][1] if len(atr_long) else (sum([tr for tr in self.__dynamic_study_data['tr_100']][1:]) / (len(self.__dynamic_study_data['tr_100'])-1)))
            atr_long.append((date, (c * self.__dynamic_study_data['tr_100'][-1]) + (1 - c) * ma[1]))
            self.__dynamic_study_indexes[Study.ATR_LONG][date] = len(atr_long) - 1

        # HHLL
        hhll_short = self.__dynamic_studies[Study.HHLL_SHORT]
        hhll_short.append((date, max(self.__dynamic_study_data['50']), min(self.__dynamic_study_data['50'])))
        self.__dynamic_study_indexes[Study.HHLL_SHORT][date] = len(hhll_short) - 1

        # print date, len(hhll_short), self.study(Study.HHLL_SHORT, date), self.__dynamic_studies[Study.HHLL_SHORT][-1]

        # Volume SMA
        vol_short = self.__dynamic_studies[Study.VOL_SHORT]
        # vol_short.append((date, float(sum(self.__dynamic_study_data['vol_50'])) / len(self.__dynamic_study_data['vol_50'])))
        vol_short.append((date, sum(self.__dynamic_study_data['vol_50']) / len(self.__dynamic_study_data['vol_50'])))
        self.__dynamic_study_indexes[Study.VOL_SHORT][date] = len(vol_short) - 1

        # print date, len(vol_short), self.study(Study.VOL_SHORT, date), self.__dynamic_studies[Study.VOL_SHORT][-1]

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
