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

###Investment Universe
*Equal-weighted investment universe*

| Agricultural  | Non-agricultural  | Currencies    | Equities      | Rates             |
|---------------|-------------------|---------------|---------------|-------------------|
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

###Process

* Automatic download
* Error processing
* Automatic Error Report?
* Automatic Error Correction? (pad, interpolate, etc.)
* Generating Continuous contract (even if provided commercially -- to cross-check)
  (Use back-adjusted connecting method)
* Generate multi-expiration overlay chart of Open Interest and Volume (for rollover decisions)
* Generating Term-structure charts
* Archiving (and Compression)

* Replicate remote DB to local desktop?

###Entities
*See Norgate for DB tables layout inspiration*

* Exchange (Ultimate original source)
* Vendor (Where it is obtained from?)
* Instrument/Ticker (Ticker/Symbol along with corporate info.)
* Price
* Corporate Action (Stock Splits, Divident adjustments, etc.)
* National Holidays

###Data Accuracy Evaluation

* Conflicting/incorrect data
* Opaque aggregation
* Corporate Action (make sure the Formulae has been applied correctly)
* Spikes (Pricing points exceedeing greatly historical volatility)
* OHLC Aggregation
* Missing Data (pad, interpolate, ignore, ... ?)
* Backfilling (See 8.3.1 in SAT)
* Account for name/code changes
