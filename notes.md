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

#####DataBase

* MySQL
    * Performance
    * Availability
    * Replication (Backup)
    * Schema update/installation

#####Execution

* Market / Exchange Micro-structure
* Transaction cost
* Test execution price across period's high-low range
* Set up "cap" on opening prices? (based on vola. stats? / observe night range)

#####Backtesting Biases

- Optimisation Bias
- Look-Ahead Bias
    + Technical bugs
    + Parameter Calculations
    + Maxima/Minima
- Survivorship Bias
- Cognitive Bias

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
* Execution confirmations and summary

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
