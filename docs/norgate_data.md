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

* NYSE Arca, US
* NYSE, US
* AMEX, US
* NASDAQ, US
* OTC, US

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
