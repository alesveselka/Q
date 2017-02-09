##Systematic Risk Allocation

###Development

#####Python

* Libraries
    * NumPy (vectorized operations)
    * SciPy (optimization algorithms)
    * pandas (time series analysis)
    * statsmodel (statistical modeling)
    * scikit-learn (statistical/machine learning)
    * IPython (interactive development)
    * matplotlib (visualization)
    * IbPy (Interactive Brokers wrapper)
    * NLTK (Natural Language Toolkit) (Sentiment analysis)
    * ScraPy (web scraping)

#####DataBase

* MySQL
    * Performance
    * Availability
    * Replication (Backup)
    * Schema update/installation
    * UTF-8 character set

* Tick data (huge datasets)
    * HDF5 (https://support.hdfgroup.org/HDF5/)
    * kdb (kx.com)
    * CSV (Flat file)?

* Data
    * Storage Requiremenets?
    * Risk-Free Rate
    * Benchmarks (S&P 500, FTSE100, DAX, CTA indexes, etc.)
    * Fundamentals?
    * Continuous Futures Contracts
    * VIX
    * Costruct less-granual timeframe from higher-granual?
    * Total Return series for Equities (not Price series)
    * Open Interest + Volume patterns for rollover decisions!

#####Execution

* Market / Exchange Micro-structure
* Transaction cost
* Test execution price across period's high-low range
* Set up "cap" on opening prices? (based on vola. stats? / observe night range)
* Strategy should be designed such that a single data point cannot skew the performance 
  of the strategy to any great extent.
* Roll Strategy (see 'Algorithmic Trading', and 'Dynamic Roll Strategies' PDF)
* Capital-Base Adjustments happen during live-trading as well - watch out! Automatize?
* Web-scraping for future Capital-Base Adj. (earnings.com)

#####Backtesting Biases

* Optimization Bias
* Look-Ahead Bias
    * Technical bugs
    * Parameter Calculations
    * Maxima/Minima
* Data-Snooping bias
* Survivorship Bias
* Primary versus Consolidated Stock Prices
      * market-on-open / market-on-close are routed to primary exchange only,
        so I'll need price from the exchange for realistic backtest
      * The close and open prices on the U.S. primary exchanges are always
        determined by an auction, while a transaction at the close on a secondary
        exchange is not the result of an auction.
      * Historical High and Low are usually consolidated numbers resulting from
        small-size trades on secondary exchanges - not representative.
* Short-Sale Constraints
  (Especially, for example, after 2008 collapse!)
  (Uptick Rule(s))
* Futures Continuous Contracts
      * Open Interest (and Volume) Crossover (Standard Roll?)
      * Adding constant to back-adjusted series to avoid negative prices?
      * Back-Adjust 'return series' VS 'price series' (p. 13 in Algorithmic Trading)
* Futures Close versus Settlement Prices
* Different 'Closing' time of different markets - need intraday data (+ bid/ask)
* Delisted/Newly-listed stocks (Equities)
* Capital-Base Adjustment (Stock Split and Dividend Adjustment)
  (Total Return Series instead of Price Series (Equities))
* Cognitive Bias
* Price Approximation without Bid/Ask info?
* FX - need historical data from venue we actually plan to trade live
* Hypothesis testing (see p. 16, Algorithmic Trading)

(Backtest double-check on Quantopian.com?)

#####Exchange Issues

* Order Types
* Price Consolidation (Average from multiple exchanges - not realistic)
* Bid / Ask Consolidation - same as above but with Bid / Ask
* Transaction Cost
    - Commissions, Fees, Taxes
    - Slippage

#####Continual Integration

* GitHub

###Deployment

#####VPS / Amazon

* High Availability
* Uptime / Restart
* Monitoring running - SMS / E-Mail problems
* Running statistics
* Execution confirmations and summary (send e-mail/SMS in case of failure/timeout)
* Second redundant server pooling first one to check availability?

###Fund

* Industry-standard Risk Management
* Reporting / Investors Relations (Margin, VaR)
* Compensation structure
* Reporting
* Peers and Industry benchmark comparisons
* "Unused" capital in bonds?
* Currency hedge
* Interest(s) and Financing!
* Team - establish credibility and authority
    - SW (RIA, SPA, Mobile, Web)
    - Trading (Long/Short Equity, second-frequncy e-mini futures, 
      (non)directional option strategies, Seasonal Futures Spreads, discretional day trading, etc.)
    - Psychology (mimetic principle)
* Cost
    - Deployment
    - Reporting
    - Taxation
* Cash In-flow/Out-flow management (**Also reflect in return reports**)

#####Currency Hedging

* Futures (Euro FX) - contract size 125,000 EUR
    - Mini Futures - contract size 62,500 EUR
    - Micro Futures - contract size 12,500 EUR
* US Dollar Futures, or Mini US Dollar Index Futures
* Forward (not available?)
* FX position (IB, Oanda)
* Calculate Rollover effect! (If held overnight, i.e. => 5pm ET)
    - Interest differential = (Base-interest - Quote interest)
      (T+2 settlement - can be 3x more if T+3 is weekend / holiday)
      (Also can be T+1, e.g. USD.CAD, USD.MXN)

* Base/Quote pair
* For non-existent pair (e.g. AUD.ZAR) I can trade synthetic
  position USD.ZAR / USD.AUD
* Buying 1 unit of pair (CAD.USD) I can as well Sell 1/y of USD.CAD
  (provided 'y' is the current quote for USD.CAD)

#####Layers

* Data
    - Data download
    - Error corrections
    - Back-Adjust contracts
* Trading
    - Signal generation
    - Position sizing
        + Correlations
        + "Trendiness" (Hurst, ...)
        + Risk managements (Kelly?)
    - Position diffs
    - Execution
* Hedge
    - Currency hedge
    - Fixed income
* Reporting
    - Margin
    - VaR
    - Stats

###Math Topics

* Statistical Stationary tests
    * Augmented Dickey-Fuller
    * Hurst Exponent
    * Variance-Ratio Test

* Sensitivity Analysis

###Stats

* Beta to SPY/S&P 500, Funds of Funds / Peers
* Sharpe ratio
* Annualized volatility
* Annualized return
* Max Drawdown (size and time)
* Stability of Returns
* Sortino ratio
* "Trendiness" via Hurst Exponent
* Also calculate stats on the time series themselves
  in addition on strategy results
* Pearson Product Moment Correlation Coefficient
* Variance-Covariance
* Mean Square Error (MSE)
* Also test the stationarity of the vehicles themselves, because their
  statistical significance is usually higher and also indicate if strategy
  will be profitable, not only based on backtest alone.

###Misc

* Fundamentals? (GDP, Leading indicators, ... ?)

###Strategies

* **Diversified Trend-Following with Futures**
* Statistical Pair trading (Mean-Reversion on Cointegrated portfolios)
* Dual Momentum
* Intraday momentum
* Trend-Following on ratios (Stocks, ETFs, Futures, etc.)
  (potentially "big-moves" universe?)
* fundamentals-driven Long/Short equity
* Commodity Spreads
* Weller hybrid system
* "Trading Room"
* Mean-Revert allocation to whole portfolio?
* Cross-Sectional Mean-Reversion (p. 104 in Algo (APR: 70 %, Sharpe > 4!))
