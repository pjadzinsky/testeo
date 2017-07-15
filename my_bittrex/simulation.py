#!/usr/bin/python
import os
import numpy as np
import pandas as pd

from my_bittrex import volume
from my_bittrex.test import test_utils

# Start a portfolio from scratch, all positions are the same at start

def main():
    state = np.ones((3,))
    if not os.path.isfile('initial_portfolio.csv'):
        target_portfolio = volume.start_new_portfolio(state, 'BTC', 10, 'target_portfolio.csv')
        target_portfolio.to_csv('initial_portfolio.csv')

    initial_portfolio = pd.read_csv('initial_portfolio.csv')

    portfolio = volume.Portfolio(target_portfolio)

    print portfolio.portfolio
    print portfolio.value('BTC')
    print '*' * 80

    for i in range(10):
        test_utils.perturb_market(volume.market, 0.1)
        adjustment = portfolio.rebalance('BTC')
        #portfolio.portfolio['Balance'] -= adjustment['delta']
        #portfolio.portfolio['Available'] -= adjustment['delta']


if __name__ == "__main__":
    main()
