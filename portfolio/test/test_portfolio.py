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
        currencies = "BTC,ETH,XRP,LTC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print p.dataframe

    def test_total_value_0(self):
        market = self.markets.first_market()
        currencies = "BTC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        computed = p.total_value(market, ['USDT', 'BTC'])
        self.assertEqual(computed, value * (1 - portfolio.COMMISION))

    def test_total_value_1(self):
        market = self.markets.first_market()
        currencies = "BTC,ETH,XRP,LTC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        computed = p.total_value(market, ['USDT', 'BTC'])
        self.assertEqual(computed, value * (1.0 - portfolio.COMMISION))

    def test_value_per_currency_0(self):
        market = self.markets.first_market()
        currencies = "BTC,ETH,XRP"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        computed = p.value_per_currency(market, ['USDT', 'BTC'])

        # computed has a row with 'USDT' that has 0 value, drop it
        computed.drop('USDT', inplace=True)

        for v in computed.values:
            self.assertAlmostEqual(v, value * (1.0 - portfolio.COMMISION) / 3)
        print computed

if __name__ == "__main__":
    unittest.main()
