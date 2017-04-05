#!/usr/bin/python


class EventType:
    MARKET_DATA = 'MARKET_DATA'
    HEARTBEAT = 'HEARTBEAT'


class Study:
    HHLL = 'HHLL'
    SMA = 'SMA'
    EMA = 'EMA'
    ATR = 'ATR'


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
    INTEREST = 'Interest'
    MARGIN_LOAN = 'Margin Loan'


class AccountAction:
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'
