##Systematic Risk Allocation

###Development

#####Python

* Libraries
    * NumPy (vectorised operations)
    * SciPy (optimisation algorithms)
    * pandas (time series analysis)
    * statsmodel (statistical modelling)
    * scikit-learn (statistical/machine learning)
    * IPython (interactive development)
    * matplotlib (visualisation)
    * IbPy (Interactive Brokers wrapper)

#####DataBase

* MySQL
    * Performance
    * Availability
    * Replication (Backup)
    * Schema update/installation
    * UTF-8 character set

* Data
    * Storage Requiremenets?
    * Risk-Free Rate
    * Benchmarks (S&P 500, FTSE100, DAX, CTA indexes, etc.)
    * Fundamentals?
    * Continuous Futures Contracts
    * VIX

#####Execution

* Market / Exchange Micro-structure
* Transaction cost
* Test execution price across period's high-low range
* Set up "cap" on opening prices? (based on vola. stats? / observe night range)
* Strategy should be designed such that a single data point cannot skew the performance of the strategy to any great extent.

#####Backtesting Biases

* Optimisation Bias
* Look-Ahead Bias
    * Technical bugs
    * Parameter Calculations
    * Maxima/Minima
* Survivorship Bias
* Cognitive Bias

(Backtest double-check on Quantopian.com?)

#####Exchange Issues

* Order Types
* Price Consolidation (Average from multiple exchanges - not realistic)
* Bid / Ask Consolidation - same as above but with Bid / Ask
* Transaction Cost
    - Commissions, Fees, Taxes
    - Slippage

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
* Reporting / Investors Relations
* Compensation structure
* Reporting
* Peers and Industry benchmark comparisons

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
* Max Drodawn (size and time)
* Stability of Returns
* Sortino ratio

###Misc

* Fundamentals? (GDP., Leading indicators, ... ?)
