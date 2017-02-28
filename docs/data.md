##Data

###Type

* Equities (and ETFs)
* Bonds (Fixed Income)
* Commodities (Futures)
* Risk-Free Rate
* Forex (FX)
* Benchmarks / Indicies (US and International)
* VIX

###Source

* Free EOD Equities
    * Yahoo Finance
    * Google Finance
    * Quandl (*best free source?*)
    * EODData (requires registration)
    * QuantQuote (S&P 500 EOD only)
    * IB?

* Commercial
    * DTN IQFeed
    * EODData (Platinum)
    * QuantQuote
    * Norgate (see Clenow referral)
    * CSI Data

###Investment Universes
**Euro based FX Futures doesn't start as early as other ones. 
  Trade FX directly instead.
  EUR has not existed until 1999; construct ECU (European Currency Unit) 
  from other currencies**

*Equal-weighted*
```
+---------------+-------------------+---------------+---------------+-------------------+
| Agricultural  | Non-agricultural  | Currencies    | Equities      | Rates             |
+---------------+-------------------+---------------+---------------+-------------------+
| Cotton        | Gasoil            | AUD/USD       | CAC 40        | Bunt              |
| Corn          | Crude oil         | GBP/USD       | DAX           | Schatz            |
| Lumber        | Heating oil       | EUR/USD       | FTSE 100      | Long gilt         |
| Live cattle   | Natural gas (HH)  | JPY/USD       | HS China      | Canadian Bankers' |
|               |                   |               | Enterprises   | Acceptance        |
| Lean hogs     | Gasoline          | NZD/USD       | Hang Seng     | US 2-year note    |
| Oats          | Gold              | EUR/CHF       | Nasdaq 100    | US 10-year note   |
| Rough rice    | Copper            | EUR/GBP       | Nikkei 225    | Eurodollar        |
| Soybeans      | Palladium         | EUR/JPY       | S&P 500       | Euroswiss         |
| Sugar         | Platinum          | CHF/USD       | EuroStoxx 50  | Euribor           |
| Wheat         | Silver            | CAD/USD       | Russell 2000  | Short sterling    |
+---------------+-------------------+---------------+---------------+-------------------+
```

*Large*
```
+-------------------+-------------------+---------------+---------------+-------------------+
| Agricultural      | Non-agricultural  | Currencies    | Equities      | Rates             |
+-------------------+-------------------+---------------+---------------+-------------------+
| Azuki red beans   | Copper            | AUD/USD       | CAC 40        | AU 10Y            |
| Coffee            | Crude oil         | CAD/USD       | DAX           | AU 3Y             |
| Corn              | Gas oil           | CHF/USD       | EuroStoxx     | AU 90 Day         |
| Cotton            | Gasoline          | EUR/USD       | FTSE 100      | Bobl              |
| Lean hogs         | Gold              | GBP/USD       | Hang Seng     | Bund              |
| Live cattle       | Heating oil       | JPY/USD       | HS China Ent. | CD 10Y            |
| Lumber            | Natural gas       | MXN/USD       | IBEX 35       | Can. Bankers' Acc.|
| Oats              | Palladium         | NOK/USD       | MSCI Taiwan   | Euribor           |
| Orange Juice      | Platinum          | NZD/USD       | Nasdaq 100    | Eurodollar        |
| Rapeseed          | Silver            | SEK/USD       | Nikkei 225    | Euroswiss         |
| Rough rice        |                   | ZAR/USD       | S&P 500       | JP 10Y            |
| Rubber            |                   |               | S&P 60        | Long gilt         |
| Soybean meal      |                   |               | SPI 200       | Schatz            |
| Soybean           |                   |               |               | Short sterling    |
| Sugar             |                   |               |               | US 10Y            |
| Wheat             |                   |               |               | US 2Y             |
|                   |                   |               |               | US 30Y            |
|                   |                   |               |               | US 5Y             |
+-------------------+-------------------+---------------+---------------+-------------------+
```

*Large, Reduced Equities*
```
+-------------------+-------------------+---------------+---------------+-------------------+
| Agricultural      | Non-agricultural  | Currencies    | Equities      | Rates             |
+-------------------+-------------------+---------------+---------------+-------------------+
| Azuki red beans   | Copper            | AUD/USD       | DAX           | AU 10Y            |
| Coffee            | Crude oil         | CAD/USD       | EuroStoxx     | AU 3Y             |
| Corn              | Gas oil           | CHF/USD       | Hang Seng     | AU 90 Day         |
| Cotton            | Gasoline          | EUR/USD       | MSCI Taiwan   | Bobl              |
| Lean hogs         | Gold              | GBP/USD       | Nasdaq 100    | Bund              |
| Live cattle       | Heating oil       | JPY/USD       | Nikkei 225    | CD 10Y            |
| Lumber            | Natural gas       | MXN/USD       | S&P 500       | Can. Bankers' Acc.|
| Oats              | Palladium         | NOK/USD       |               | Euribor           |
| Orange Juice      | Platinum          | NZD/USD       |               | Eurodollar        |
| Rapeseed          | Silver            | SEK/USD       |               | Euroswiss         |
| Rough rice        |                   | ZAR/USD       |               | JP 10Y            |
| Rubber            |                   |               |               | Long gilt         |
| Soybean meal      |                   |               |               | Schatz            |
| Soybean           |                   |               |               | Short sterling    |
| Sugar             |                   |               |               | US 10Y            |
| Wheat             |                   |               |               | US 2Y             |
|                   |                   |               |               | US 30Y            |
|                   |                   |               |               | US 5Y             |
+-------------------+-------------------+---------------+---------------+-------------------+
```

*Financially Heavy*
```
+-------------------+-------------------+---------------+---------------+-------------------+
| Agricultural      | Non-agricultural  | Currencies    | Equities      | Rates             |
+-------------------+-------------------+---------------+---------------+-------------------+
| Coffee            | Copper            | AUD/USD       | CAC 40        | AU 10Y            |
| Corn              | Crude oil         | CAD/USD       | DAX           | AU 3Y             |
| Cotton            | Gas oil           | CHF/USD       | EuroStoxx     | AU 90 Day         |
| Lean hogs         | Gasoline          | EUR/USD       | FTSE 100      | Bobl              |
| Live cattle       | Gold              | GBP/USD       | Hang Seng     | Bund              |
| Soybean meal      | Heating oil       | JPY/USD       | IBEX 35       | CD 10Y            |
| Soybean oil       | Natural gas       | MXN/USD       | MSCI Taiwan   | Can. Bankers' Acc.|
| Soybean           | Platinum          | NOK/USD       | Nasdaq 100    | Euribor           |
| Sugar             | Silver            | NZD/USD       | Nikkei 225    | Eurodollar        |
| Wheat             |                   | SEK/USD       | S&P 500       | Euroswiss         |
|                   |                   | ZAR/USD       | S&P 60        | JP 10Y            |
|                   |                   |               | SPI 200       | Long gilt         |
|                   |                   |               |               | Schatz            |
|                   |                   |               |               | Short sterling    |
|                   |                   |               |               | US 10Y            |
|                   |                   |               |               | US 2Y             |
|                   |                   |               |               | US 30Y            |
|                   |                   |               |               | US 5Y             |
+-------------------+-------------------+---------------+---------------+-------------------+
```

*Commodity Heavy*
```
+-------------------+-------------------+---------------+---------------+-------------------+
| Agricultural      | Non-agricultural  | Currencies    | Equities      | Rates             |
+-------------------+-------------------+---------------+---------------+-------------------+
| Azuki red beans   | Copper            | AUD/USD       | EuroStoxx 50  | Bund              |
| Coffee            | Crude oil         | CAD/USD       | Hang Seng     | Can. Bankers' Acc.|
| Corn              | Gasoline          | EUR/USD       | Nasdaq 100    | Eurodollar        |
| Cotton            | Gold              | GBP/USD       | Nikkei 225    | Long gilt         |
| Lean hogs         | Heating oil       | JPY/USD       | S&P 500       | US 10Y            |
| Live cattle       | Natural gas       |               |               |                   |
| Lumber            | Palladium         |               |               |                   |
| Oats              | Platinum          |               |               |                   |
| Orange Juice      | Silver            |               |               |                   |
| Rapeseed          |                   |               |               |                   |
| Rough rice        |                   |               |               |                   |
| Rubber            |                   |               |               |                   |
| Soybean meal      |                   |               |               |                   |
| Soybean           |                   |               |               |                   |
| Sugar             |                   |               |               |                   |
| Wheat             |                   |               |               |                   |
+-------------------+-------------------+---------------+---------------+-------------------+
```
###Process

**SET UP MYSQL CONFIG BEFORE USING (e.g. max_allowed_packet, etc.)**

* Automatic download
* Error processing
* Automatic Error Report?
* Automatic Error Correction? (pad, interpolate, etc.)
* Generating Continuous contract (even if provided commercially -- to cross-check)
  (Use back-adjusted connecting method)
    * **Back-Adjusted Price Series for 'price-difference spreads' (e.g. calendar)**
    * Back-Adjusted Return Series for 'ratio-or-prices spreads'
* Generate multi-expiration overlay chart of Open Interest and Volume (for rollover decisions)
* Generating Term-structure charts
* Archiving (and Compression)

* Check last EOD data with the one from actual Exchange website? (web-scrape specs pages)
* Replicate remote DB to local desktop?

###Entities
*See Norgate for DB tables layout inspiration*

* Exchange (Ultimate original source)
* Vendor (Where it is obtained from?)
* Instrument/Ticker (Ticker/Symbol along with corporate info.)
* Price
* Corporate Action (Stock Splits, Divident adjustments, etc.)
* National Holidays
* Trading hours!

###Data Accuracy Evaluation

* Conflicting/incorrect data
* Opaque aggregation
* Corporate Action (make sure the Formulae has been applied correctly)
* Spikes (Pricing points exceedeing greatly historical volatility)
* OHLC Aggregation
* Missing Data (pad, interpolate, ignore, ... ?)
* Backfilling (See 8.3.1 in SAT)
* Account for name/code changes
