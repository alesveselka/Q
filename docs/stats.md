##Stats

###Prediction and Inference

#####Prediction

* Parametric Model
    - require specification (assumption) of form of 'f' function 
    - OLS (ordinary least squares) in linear settings
* Non-Parametric Model
    - more flexible, but prone to overfitting

######Supervised and Unsupervised Learning

* Supervised model requires that for each predictor X(j) there is an associated 
  response Y(j)
* In Unsupervised model, there is no corresponding response Y(j) for any
  particular predictor X(j)

###Techniques

#####Regression
*Supervised Machine Learning. Tries to model the relationship between a dependent 
variable (response) and set of independent variables (predictors).*

* Linear Regression (linear relationships between the predictors and response)
* Logistic Regression (categorical/classification tool) (Maximum Likelihood Estimation)

#####Classification
*Aim to classify an observation (similar to a predictor) into a set of pre-defined
categories, based on features associated with observation.*

* Logistic Regression
* Linear/Quadratic Discriminant Analysis
* Support Vector Machines (SVM)
* Artificial Neural Neworks (ANN)

#####Time Series Models
*Mixed-subset of regression and classification, that make deliberate use 
of the temporal ordering of the series.*

* Linear Autoregressive Integrated Moving Average (ARIMA)
  (Variations in the absolute value of a time series)
* Autoregressive Conditional Heteroskedasticity (ARCH)
  (Model variance/volatility of time series over time)

* Discrete Time Series - contain finite values
* Continuous Times Series
    - Geometric Brownian Motion
    - Heston Stochastic Volatility
    - Ornstein-Uhlenbeck

###Time Series Analysis

#####Mean Reversion

* Ornstein-Uhlenbeck process
* Augmented Dickey-Fuller (ADF) Test
* Hurst Exponent
  Testing Stationarity. **Strong Stationarity** is when *joint probability distribution* 
  is invariant under translations in time or space.
    * H < 0.5 -- The time series is mean reverting
    * H = 0.5 -- The time series is a Geometrical Brownian Motion
    * H > 0.5 -- The time series is trending
* Cointegrated Augmented Dickey-Fuller (CADF)
  Determines optimal hedge ratio by performing a linear regression aginst the two 
  time series and then test for stationarity under the linear combination.
