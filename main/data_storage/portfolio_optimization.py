#!/usr/bin/python

from math import sqrt


terms = []
markets = [
    {'deviation': 0.1},
    {'deviation': 0.1}
]
weight = 1.0 / float(len(markets))
pairs = [
    {
        'markets': [markets[0], markets[1]],
        'correlation': 0.0
    }
]

for market in markets:
    terms.append(weight**2 * market['deviation']**2)

for pair in pairs:
    terms.append(2 * weight*pair['markets'][0]['deviation'] * weight*pair['markets'][1]['deviation'] * pair['correlation'])

print 'Deviation', sum(terms)
print 'Volatility: %.4f' % sqrt(abs(sum(terms)))
# print 'Volatility:', '{:.2%}'.format(sqrt(abs(sum(terms))))
