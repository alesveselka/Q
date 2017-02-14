##Norgate Data

###Tables

#####Exchange
```
+-----------------------+
| exchange              |
+-----------------------+
| id                    |
| abbrev                |
| name                  |
| city                  |
| country               |
| timezone              |
+-----------------------+
```
#####Market
```
+-----------------------+
| market                |
+-----------------------+
| id                    |
| name                  |
| code                  | use as primary key?
| instrument            | e.g. 'Futures', 'Spot'
| data_vendor           | 'Norgate' in this instance
| exchange_id           | (use duplicate instead of 'id' for performance?)
| group_id              | (use duplicate instead of 'id' for performance?)
| contract_size         |
| quotation             |
| tick_size             |
| tick_value            |
| point_value           |
| currency              |
| last_trading_day      |
| first_notice_day      |
| trading_hours?        |
| session/platform      |
| volume_offset         |
| oi_offset             |
| delivery_months       |
+-----------------------+
```
#####Delivery Month
```
+-----------------------+
| delivery_month        |
+-----------------------+
| code (primary key)    |
| name                  |
+-----------------------+
```
#####Contract
```
+-----------------------+
| contract              |
+-----------------------+
| id                    |
| market_id             |
| delivery_date         | (month + year)
| expiration_date       |
| code                  | (market + month + year) as primary id?
| price_date            |
| open_price            |
| high_price            |
| low_price             |
| last_price            |
| settle_price          | usually equals close price
| volume                |
| open_interest         |
| created_date          |
| last_update_date      |
+-----------------------+
```
#####Continuous Back_adjusted contract
```
+-------------------------------+
| continuous_back_adjusted      |
+-------------------------------+
| id                            |
| market_id                     |
| roll_strategy                 |
| price_date                    |
| open_price                    |
| high_price                    |
| low_price                     |
| last_price                    |
| settle_price                  |
| volume                        |
| open_interest                 |
| created_date                  |
| last_updated_date             |
+-------------------------------+
```
#####Continuous Spliced contract
```
+---------------------------+
| continuous_spliced        |
+---------------------------+
| id                        |
| market_id                 |
| price_date                |
| open_price                |
| high_price                |
| low_price                 |
| last_price                |
| settle_price              |
| volume                    |
| open_interest             |
| created_date              |
| last_updated_date         |
+---------------------------+
```
#####Spot markets 
(Not needed - see 'market' schema)
```
+-----------------------+
| spot                  |
+-----------------------+
| id                    | do I need 'id'?
| market_id             |
| code                  |
| note                  |
| created_date          |
| last_updated_date     |
+-----------------------+
```
#####Group (Sector)
```
+-----------------------+
| group                 |
+-----------------------+
| id                    |
| name                  |
| standard              |
+-----------------------+
```
#####Holidays
```
+-----------------------+
| holidays              |
+-----------------------+
| id                    |
| exchange_id           |
| holiday               |
| name                  |
+-----------------------+
```

###Static Data

#####Exchange

* Stocks
    - Australian Securities Exchange (ASX)
    - NYSE Arca, US
    - NYSE, US
    - AMEX, US
    - NASDAQ, US
    - OTC, US
    - (Indices)

* Futures
    - Australian Securities Exchange (ex SFE)
    - Chicago Board Options Exchange (CBOE)
    - CME Group (ex CBOT)
    - CME Group (ex CME)
    - CME Group (ex NYMEX/COMEX)
    - CME Group (ex KCBT)
    - Eurex
    - Hong Kong Stock Exchange (HKEx)
    - ICE Futures Canada
    - ICE Futures Europe
    - ICE Futures US
    - Kansas City Board of Trade (KCBT)
    - Korea Exchange (KRX)
    - Minneapolis Grain Exchange (MGEX)
    - Montreal Exchange (MX) (Bourse de Montreal)
    - NYSE Euronext (ex LIFFE)
    - Singapore Exchange (Futures) (SGX)

#####Market

* Securities
    - Equities
        + Common Stock (Common)
        + Preferred Stock (PFD)
        + Warrants (Warrant)
        + American Depository Receipts (ADR)
        + Closed-End Fund (CEF)
        + Exchange Traded Debt (DEBT)
        + Exchange Traded Fund (ETF)
        + Exchange Traded Notes (ETN)
        + Real Estate Investment Trust (REIT)
        + Special Investment Product (SIP)
        + Master Limited Partnership (UNIT)
        + Royalty Trust (UNIT)
        + (Market Breadth Indicators)

#####Groups (Sectors)

* Norgate (Futures)
    - Currency
    - Food / Fiber
    - Grain / Oilseed
    - Index
    - Interest Rate
    - Meat / Livestock
    - Metal
    - Oil / Energy

#####Delivery Months

* January: F
* February: G
* March: H
* April: J
* May: K
* June: M
* July: N
* August: Q
* September: U
* October: V
* November: X
* December: Z
