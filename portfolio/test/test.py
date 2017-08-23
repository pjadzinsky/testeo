#!/usr/bin/python
import unittest

import pandas as pd

from portfolio import portfolio
from markets import recreate_markets

class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.markets = recreate_markets.get_markets()
        self.times = recreate_markets.times()

    def test_total_value(self):
        index = ['BTC']
        available = [1]
        balance = [1]

        df = pd.DataFrame({'Available': available, 'Balance': balance}, index=index)
        positions = portfolio.Portfolio(dataframe=df)
        for time in self.times:
            market = recreate_markets.market_at_time(time)
            computed = positions.total_value(market, ['BTC', 'USDT'])
            print computed

if __name__ == "__main__":
    unittest.main()
