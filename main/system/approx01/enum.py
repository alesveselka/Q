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
    AUD='AUD',
    GBP='GBP',
    CAD='CAD',
    EUR='EUR',
    JPY='JPY',
    CHF='CHF',
    USD='USD'
)

OrderType = enum(
    'OrderType',
    BTO='BTO',
    BTC='BTC',
    STO='STO',
    STC='STC',
)

OrderResultType = enum(
    'OrderResultType',
    FILLED='FILLED'
)

TransactionType = enum(
    'TransactionType',
    MTM_POSITION='MTM Position',
    MTM_FX_BALANCE='MTM Fx Balance',
    COMMISSION='Commission',
    INTEREST='Interest',
    MARGIN_LOAN='Margin Loan'
)

AccountAction = enum(
    'AccountAction',
    CREDIT='CREDIT',
    DEBIT='DEBIT'
)
