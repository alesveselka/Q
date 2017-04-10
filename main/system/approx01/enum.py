#!/usr/bin/python


class EventType:
    MARKET_OPEN = 'MARKET_OPEN'
    MARKET_CLOSE = 'MARKET_CLOSE'
    EOD_DATA = 'EOD_DATA'


class Study:
    ATR_LONG = 'atr_long'
    ATR_SHORT = 'atr_short'
    VOL_SHORT = 'vol_short'
    SMA_LONG = 'sma_long'
    SMA_SHORT = 'sma_short'
    HHLL_LONG = 'hhll_long'
    HHLL_SHORT = 'hhll_short'


class Direction:
    LONG = 'LONG'
    SHORT = 'SHORT'


class SignalType:
    ENTER = 'ENTER'
    EXIT = 'EXIT'


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


class TransactionType:
    MTM_TRANSACTION = 'MTM Transaction'
    MTM_POSITION = 'MTM Position'
    FX_BALANCE_TRANSLATION = 'Fx Balance Translation'
    COMMISSION = 'Commission'
    INTEREST_CHARGED = 'Interest Charged'
    INTEREST_PAID = 'Interest Paid'
    MARGIN_LOAN = 'Margin Loan'
    INTERNAL_FUND_TRANSFER = 'Fund Transfer (Internal)'


class AccountAction:
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'


class Table:
    class Futures:
        CODE = 0
        PRICE_DATE = 1
        OPEN_PRICE = 2
        HIGH_PRICE = 3
        LOW_PRICE = 4
        SETTLE_PRICE = 5
        VOLUME = 6
        # TEST = Column('test_column', 3, int)
