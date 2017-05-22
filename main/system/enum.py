#!/usr/bin/python


class EventType:
    MARKET_OPEN = 'MARKET_OPEN'
    MARKET_CLOSE = 'MARKET_CLOSE'
    EOD_DATA = 'EOD_DATA'
    COMPLETE = 'COMPLETE'


class Study:
    ATR_LONG = 'atr_long'
    ATR_SHORT = 'atr_short'
    VOL_SHORT = 'vol_short'
    MA_LONG = 'ma_long'
    MA_SHORT = 'ma_short'
    HHLL_LONG = 'hhll_long'
    HHLL_SHORT = 'hhll_short'


class Direction:
    LONG = 'LONG'
    SHORT = 'SHORT'


class SignalType:
    ENTER = 'ENTER'
    EXIT = 'EXIT'
    ROLL_ENTER = 'ROLL_ENTER'
    ROLL_EXIT = 'ROLL_EXIT'


class Currency:
    AUD = 'AUD'
    GBP = 'GBP'
    CAD = 'CAD'
    EUR = 'EUR'
    JPY = 'JPY'
    CHF = 'CHF'
    USD = 'USD'


class OrderType:
    BTO = 'BTO'
    BTC = 'BTC'
    STO = 'STO'
    STC = 'STC'


class OrderResultType:
    FILLED = 'FILLED'
    REJECTED = 'REJECTED'


class TransactionType:
    MTM_TRANSACTION = 'MTM Transaction'
    MTM_POSITION = 'MTM Position'
    FX_BALANCE_TRANSLATION = 'Fx Balance Translation'
    COMMISSION = 'Commission'
    BALANCE_INTEREST = 'Balance Interest'
    MARGIN_INTEREST = 'Margin Interest'
    MARGIN_LOAN = 'Margin Loan'
    INTERNAL_FUND_TRANSFER = 'Fund Transfer (Internal)'


class AccountAction:
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'


class AccountRecord:
    EQUITY = 0
    FX_BALANCE = 1
    MARGIN_LOANS = 2


class Interval:
    DAILY = 'DAILY'
    MONTHLY = 'MONTHLY'
    YEARLY = 'YEARLY'


class Table:
    class Market:
        CODE = 0
        PRICE_DATE = 1
        OPEN_PRICE = 2
        HIGH_PRICE = 3
        LOW_PRICE = 4
        SETTLE_PRICE = 5
        VOLUME = 6

    class CurrencyPair:
        PRICE_DATE = 0
        OPEN_PRICE = 1
        HIGH_PRICE = 2
        LOW_PRICE = 3
        LAST_PRICE = 4

    class InterestRate:
        PRICE_DATE = 0
        IMMEDIATE_RATE = 1
        THREE_MONTHS_RATE = 2

    class Study:
        DATE = 0
        VALUE = 1
        VALUE_2 = 2

    class Simulation:
        ID = 0
        NAME = 1
        PARAMS = 2
        TRADING_MODEL_ID = 3
        TRADING_PARAMS = 4
        STUDIES = 5
        ROLL_STRATEGY_ID = 6
        INVESTMENT_UNIVERSE = 7
