#!/usr/bin/python
import unittest

import pandas as pd

from portfolio import portfolio
from market import market

class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.markets = market.Markets(3600, 0)

    def test_from_largest_markets(self):
        market = self.markets.first_market()
        N = 3
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_largest_markes(market, N, base, value)
        print p.dataframe


if __name__ == "__main__":
    unittest.main()
