#!/usr/bin/python


def enum(name, **enums):
    result = type(name, (), enums)
    result.items = enums.items()
    return result


EventType = enum(
    'EventType',
    MARKET_DATA='MARKET_DATA',
    HEARTBEAT='HEARTBEAT'
)

Study = enum(
    'Study',
    HHLL='HHLL',
    SMA='SMA',
    EMA='EMA',
    ATR='ATR'
)

Direction = enum(
    'Direction',
    LONG='LONG',
    SHORT='SHORT'
)

# TODO rename to 'ENTER' and 'EXIT' (so not to confuse with OHLC names)
SignalType = enum(
    'SignalType',
    OPEN='OPEN',
    CLOSE='CLOSE'
)

Currency = enum(
    'Currency',
    AUD='Australian Dollar',
    GBP='British Pound',
    CAD='Canadian Dollar',
    EUR='Euro',
    JPY='Japanese Yen',
    CHF='Swiss Franc',
    USD='United States Dollar'
)

OrderType = enum(
    'OrderType',
    BTO='BTO',
    BTC='BTC',
    STO='STO',
    STC='STC',
)

TransactionType = enum(
    'TransactionType',
    POSITION_MTM='POSITION_MTM',
    FX_BALANCE_MTM='FX_BALANCE_MTM',
    COMMISSION='COMMISSION',
    INTEREST='INTEREST',
    MARGIN_LOAN='MARGIN_LOAN'
)

AccountChange = enum(
    'AccountChange',
    CREDIT='CREDIT',
    DEBIT='DEBIT'
)
