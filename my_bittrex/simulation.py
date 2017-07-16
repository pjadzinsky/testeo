#!/usr/bin/python
import os
import numpy as np
import pandas as pd

from my_bittrex import volume
from my_bittrex.test import test_utils


def main():
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'
    state = np.ones((3,))
    base_currency = 'BTC'
    value = 10

    market = volume.Market()
    initial_portfolio = volume.start_new_portfolio(market, state, base_currency, value)

    print initial_portfolio.portfolio
    for i in range(1):
        test_utils.perturb_market(market, 0.1)
        adjustment = initial_portfolio.rebalance(market, state, initial_portfolio, 'BTC', 0.1)
        print adjustment


if __name__ == "__main__":
    main()
