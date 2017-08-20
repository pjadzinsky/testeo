#!/usr/bin/python
import unittest

from markets import recreate_markets
from markets import market_operations
from portfolio import portfolio


class TestState(unittest.TestCase):
    def test_uniform_state_1(self):
        first_market = recreate_markets.first_market()
        print portfolio.uniform_state(first_market, 5, include_usd=True)

    def test_uniform_state_2(self):
        first_market = recreate_markets.first_market()
        print portfolio.uniform_state(first_market, 5, include_usd=False)

    def test_uniform_state_3(self):
        first_market = recreate_markets.first_market()
        print portfolio.uniform_state(first_market, 13, include_usd=True)

    def test_uniform_state_4(self):
        first_market = recreate_markets.first_market()
        print portfolio.uniform_state(first_market, 3, include_usd=False)

class TestStartPortfolio(unittest.TestCase):
    def test_start_portfolio(self):
        first_market = recreate_markets.first_market()
        state = portfolio.uniform_state(first_market, 20, True)
        base = 'BTC'
        value = 10
        first_portfolio = portfolio.start_portfolio(first_market, state, base, value)
        print first_portfolio.value_per_currency(first_market, ['BTC', 'USDT'])
        print first_portfolio.total_value(first_market, ['BTC'])

class TestMarketOperations(unittest.TestCase):
    def test_variance(self):
        markets = recreate_markets.get_markets()
        variances_df = market_operations.variance(markets)
        print variances_df


if __name__ == "__main__":
    unittest.main()
