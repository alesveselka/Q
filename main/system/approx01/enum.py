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
