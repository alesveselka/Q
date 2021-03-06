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

#####Mean Reversion (Time-Series Mean Reversion)

* Ornstein-Uhlenbeck process
* Augmented Dickey-Fuller (ADF) Test (test mean-reversion)
* Hurst Exponent
  Testing Stationarity. **Strong Stationarity** is when *joint probability distribution* 
  is invariant under translations in time or space.
    * H < 0.5 -- The time series is mean reverting
    * H = 0.5 -- The time series is a Geometrical Brownian Motion
    * H > 0.5 -- The time series is trending
* Variance Ratio Test
    * 'h' = 1 -- rejection of random walk hypothesis
    * 'h' = 0 -- may be random walk
    * 'p' -- probability of null (random walk) hypothesis being true
* Half-Life of mean-reversion (test how quickly a price series reverts to its mean)

* Cointegrated Augmented Dickey-Fuller (CADF) (*suitable only for pair of price series*)
  Determines **optimal hedge ratio** by performing a linear regression against the two 
  time series and then test for stationarity under the linear combination.
  (**Cointegration** = stationary linear combination of several non-stationary
                       price series.)
* Johansen Test (*suitable to any number of price series*)

###Forecasting

#####Forecasting Performance measures

* Hit-Rate
  How many times did we predict the correct direction, as a percentage of all predictions?
* Confusion Matrix (Contingency Table)
  How many times did we predict 'up' correctly, and how many times did we 
  predict 'down' correctly?

#####Classification models

* Supervised Classification
  - Naive Bayes
  - Logistic Regression
    E.g. for measure the relationship between a *binary categorical dependent variable* 
    (i.e. 'up' or 'down' periods) and multiple independent *continuous variables*, such as
    lagged percentage returns of a financial asset.
  - Discriminant Analysis
      + Linear Discriminant Analysis (LDA)
      + Quadratic Discriminant Analysis (QDA)
  - Support Vector Machines (SVM) (Support Vector Classifier (SVC) - nonlinear)
  - Decision Trees(DT) and Random Forests
    DT partition a space into a hierarchy of boolean choices that lead to a categorization
    or grouping based on the respective decisions.
* Unsupervised learning
  - Principal Component Analysis (PCA)

###Model Selection

#####Cross Validation
*Technique used to assess how a statistical model will generalize to new data
that it has not been seen before. Usually used on predictive models.*

* Train / Test Split (2-fold cross validation)
* k-fold cross validation

#####Others

* Autocorrelation
* Mean Squared Error (MSE)
* Taylor-series expansion
* Kalman filter (market-makers favorite model for mean price estimate, p. 83 in Algo)
