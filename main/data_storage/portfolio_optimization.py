#!/usr/bin/python

import numpy as np
import cvxopt as opt
import matplotlib.pyplot as plt
from math import sqrt
from itertools import combinations
from itertools import product
from cvxopt import blas, solvers


def rand_weights(n):
    """
    Produces n random weights that sum to 1
    """
    k = np.random.rand(n)
    return k / sum(k)


def random_portfolio(returns):
    """
    Returns the mean and standard deviation of returns for a random portfolio
    """
    p = np.asmatrix(np.mean(returns, axis=1))
    w = np.asmatrix(rand_weights(returns.shape[0]))
    C = np.asmatrix(np.cov(returns))
    mu = w * p.T
    sigma = np.sqrt(w * C * w.T)

    return random_portfolio(returns) if sigma > 2 else mu, sigma


def optimal_portfolio(returns):
    """
    From Quantopian article
    https://blog.quantopian.com/markowitz-portfolio-optimization-2/
    """
    n = len(returns)
    returns = np.asmatrix(returns)

    N = 100
    mus = [10**(0.5 * t/N - 1.0) for t in range(N)]

    # Convert to cvxopt matrices
    S = opt.matrix(np.cov(returns))
    pbar = opt.matrix(np.mean(returns, axis=1))

    # Create constraint matrices
    G = -opt.matrix(np.eye(n))  # negative n x n identity matrix
    h = opt.matrix(0.0, (n, 1))
    A = opt.matrix(1.0, (1, n))
    b = opt.matrix(1.0)

    # Calculate efficient frontier weights  using quadratic programming
    portfolios = [solvers.qp(mu*S, -pbar, G, h, A, b)['x'] for mu in mus]

    # Calculate risk and returns for frontier
    returns = [blas.dot(pbar, x) for x in portfolios]
    risks = [np.sqrt(blas.dot(x, S*x)) for x in portfolios]

    # Calculate the 2nd degree polynomial of the frontier curve
    m1 = np.polyfit(returns, risks, 2)
    x1 = np.sqrt(m1[2] / m1[0])

    # Calculate the optimal portfolio
    wt = solvers.qp(opt.matrix(x1 * S), -pbar, G, h, A, b)['x']
    return np.asarray(wt), returns, risks



n_assets = 4
n_obs = 1000
return_vec = np.random.randn(n_assets, n_obs)

# plt.plot(return_vec.T, alpha=0.4)
# plt.xlabel('time')
# plt.ylabel('returns')
# plt.show()

n_portfolios = 500
means, stds = np.column_stack([random_portfolio(return_vec) for _ in xrange(n_portfolios)])

# plt.plot(stds, means, 'o', markersize=5)
# plt.xlabel('std')
# plt.ylabel('mean')
# plt.title('Mean and standard deviation of returns of randomly generated portfolios')
# plt.show()

weights, returns, risks = optimal_portfolio(return_vec)

plt.plot(stds, means, 'o', markersize=5)
plt.xlabel('std')
plt.ylabel('mean')
plt.plot(risks, returns, 'y-o')
plt.show()

print weights


# ========================================================================================================== #

# weights = map(lambda n: n / 10.0, range(3))
# weight_combinations = list(product(weights, repeat=3))
# markets = 'ABC'
# market_combinations = list(combinations(markets, 2))
# market_correlations = [('%s%s' % m, n[i]) for n in weight_combinations for i, m in enumerate(market_combinations)]

# terms = []
# w = 1.0 / float(len(markets))
# for c in market_correlations:
#     for m in market_combinations:
#         # terms = []
#         # terms.append(w**2 * 0.1**2)
#         # terms.append(2 * w*0.1 * w*0.1 * c)
#         print '%s%s' % m, c['%s%s' % m]
#     print '-' * 50

# for market in markets:
#     terms.append(market['weight']**2 * market['deviation']**2)
#
# for pair in pairs:
#     w1 = pair['markets'][0]['weight']
#     d1 = pair['markets'][0]['deviation']
#     w2 = pair['markets'][1]['weight']
#     d2 = pair['markets'][1]['deviation']
#     terms.append(2 * w1*d1 * w2*d2 * pair['correlation'])
#
# print 'Deviation', sum(terms)
# print 'Volatility: %.4f' % sqrt(abs(sum(terms)))
# print 'Volatility:', '{:.2%}'.format(sqrt(abs(sum(terms))))

# print weights
# print ''
# for w in weight_combinations:
#     print w
# print len(weight_combinations)
# for n in market_combinations:
#     print n
# for c in market_correlations:
#     print c
# print len(market_correlations)

# +-----------------+-------------------+-----------------------+
# | Level 1         | Level 2           | Level 3               |
# +-----------------+-------------------+-----------------------+
# | Corr. group 1   | Futures group     | Futures instrument    |
# +-----------------+-------------------+-----------------------+
# | Corr. group 2   | Futures group     | Futures instrument    |
# +-----------------+-------------------+-----------------------+
# | Corr. group 3   | Futures group     | Futures instrument    |
# +-----------------+-------------------+-----------------------+
