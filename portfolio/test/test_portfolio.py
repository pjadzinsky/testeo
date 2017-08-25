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

    def test_from_currencies_1(self):
        market = self.markets.first_market()
        currencies = "USDT"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print p.dataframe

    def test_from_currencies_2(self):
        market = self.markets.first_market()
        currencies = "BTC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print p.dataframe

    def test_from_currencies_3(self):
        market = self.markets.first_market()
        currencies = "BTC,USDT"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print p.dataframe

    def test_from_currencies_4(self):
        market = self.markets.first_market()
        currencies = "BTC,ETH,XRP,LTC,BCC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print p.total_value(market, ['USDT', 'BTC'])
        print p.dataframe

    def test_total_value(self):
        market = self.markets.first_market()
        currencies = "BTC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        computed = p.total_value(market, ['USDT', 'BTC'])
        self.assertEqual(computed, value * (1 - portfolio.COMMISION))

if __name__ == "__main__":
    unittest.main()
