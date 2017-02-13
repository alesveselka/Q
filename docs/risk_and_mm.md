##Risk and Money Management

###Sources of risk

* Strategy (model) risk
  Most of the backtesting issues
  Design and implementation based on statistical model
* Portfolio risk
    - Strategy correlation (Pearson Product Moment Correlation Coefficient)
      (Consider 'rolling correlation' - correlations are not static)
* Market risk
* Counterparty (Credit) risk
* Operational risk
    - Infrastructure (technology)
    - IT
    - Regulatory and Legal changes

###Money Management

* Kelly Criterion
  Leverage: size of portfolio / account equity
* CPPI (Constant Proportion Portfolio Insurance)
  (Kelly set to max DD)

###Risk Management

* Value-at-Risk (VaR)
  Estimate, under a given degree of confidence, of the size of a loss
  from a portfolio over a given time period.
    * Assumptions:
        - Standard Market Conditions
        - Volatilities and Correlations
        - Normality of Returns
* CPPI (Constant Proportion Portfolio Insurance)
  (Kelly set to max DD. Use per-strategy)
* Monte-Carlo with backtested returns instead of Kelly,
  to get more realistic picture of fat-tails distribution
* Stress tests - simulate situation of well-knows crisis (2008, Flash Crash, etc.)

###Trade Management

* (E-mini 2:1:1?)

###Leading Risk Indicators

* VIX
* TED spread (p. 185 in Algo)
* Yield curve
* Fundamentals - Housing, Customer Sentiment, Purchasing-Managers, etc.

###Other

* Return series (as opposed to price series) almost always mean-revert!
* Use Pareto-Levy distribution as better approximation than Gaussian
