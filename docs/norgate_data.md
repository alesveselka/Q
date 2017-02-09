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
| currency              |  
| timezone_offset       |  just record 'timezone' and calculate offset?
| created_date          |  
| last_updated_date     |  
+-----------------------+
```
#####Market
```
+-----------------------+  
| market                |  
+-----------------------+  
| id                    |  
| name                  |  
| code                  |  
| instrument (futures)  |  
| exchange_id           |  
| group_id              |  
| contract_size         |  
| quotation             |  
| tick_size             |  
| tick_value            |  
| point_value           |  
| currency              |  
| last_trading_day      |  
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
| month                 |  
+-----------------------+  
```
#####Contract
```
+-----------------------+  
| contract              |  
+-----------------------+  
| id                    |  
| market_id             |  
| delivery_month        |  
| code                  |   (market + month + year) as primary id?
| price_date            |  
| open_price            |  
| high_price            |  
| low_price             |  
| close_price           |   or 'last price'?
| settle_price          |   usually equals close price
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
| close_price                   |  
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
| close_price               |  
| settle_price              |  
| volume                    |  
| open_interest             |  
| created_date              |  
| last_updated_date         |  
+---------------------------+  
```
#####Cash markets
```
+-----------------------+  
| cash                  |  
+-----------------------+  
| id                    |   do I need 'id'?
| market_id             |  
| code                  |  
+-----------------------+  
```
#####Group (Sector)
```
+-----------------------+  
| group                 |  
+-----------------------+  
| id                    |  
| name                  |  
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
