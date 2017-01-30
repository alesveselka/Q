#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


if __name__ == '__main__':
    data = pd.io.parsers.read_csv(
        'equity.csv', header=0, parse_dates=True, index_col=0
    )

    # Plot three charts:
    #   Equity curve
    #   period returns
    #   drawdowns
    fig = plt.figure()
    # Set the outer color to white
    fig.patch.set_facecolor('white')

    # Plot the equity curve
    ax1 = fig.add_subplot(311, ylabel='Portfolio value: %s')
    data['equity_curve'].plot(ax=ax1, color='blue', lw=2.)
    plt.grid(True)

    # Plot the returns
    ax2 = fig.add_subplot(312, ylabel='Period returns: %s')
    data['returns'].plot(ax=ax2, color='black', lw=2.)
    plt.grid(True)

    # Plot the drawdowns
    ax3 = fig.add_subplot(313, ylabel='Drawowns: %s')
    data['drawdown'].plot(ax=ax3, color='red', lw=2.)
    plt.grid(True)

    # Plot the figure
    plt.show()
