##Data

###Type

* Futures
* Risk-Free Rate
* Forex (FX)
* Benchmarks / Indicies
* Equities
* Bonds
* VIX

###Source

* Free EOD Equities
    * Yahoo Finance
    * Google Finance
    * QuantQuote (S&P 500 EOD only)
    * EODData (requires registration)

###Process

* Automatic download
* Error processing
* Automatic Error Report?
* Automatic Error Correction? (pad, interpolate, etc.)
* Generating Continuous contract
* Archiving (and Compression)

* Replicate remote DB to local desktop?

###Entities

* Exchange (Ultimate original source)
* Vendor (Where it is obtained from?)
* Instrument/Ticker (Ticker/Symbol along with corporate info.)
* Price
* Corporate Action (Stock Splits, Divident adjustments, etc.)
* National Holidays

###Data Accuracy Evaluation

* Corporate Action (make sure the Formulae has been applied correctly)
* Spikes (Pricing points exceedeing greatly historical volatility)
* OHLC Aggregation
* Missing Data (pad, interpolate, ignore, ... ?)
