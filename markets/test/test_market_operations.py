#!/usr/bin/python
import unittest

import pandas as pd

from markets import market_operations

class TestMarketOperations(unittest.TestCase):
    def setUp(self):
        last = [1, 10, 20]
        BaseVolume = [1, 1, 1]
        Volume = [10, 10, 10]

        self.market = pd.DataFrame({'last': last, 'BaseVolume': BaseVolume, 'Volume': Volume},
                                   index=['USDT-A', 'A-B', 'A-C'])

    def test_currency_value(self):
        computed = market_operations.volume(self.market, ['A', 'USDT'])
        expected = 1 * 1 + 10 * 1 * 10 + 20 * 1 * 1


if __name__ == "__main__":
    unittest.main()
