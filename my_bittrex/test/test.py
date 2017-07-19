#!/usr/bin/python

import json
import mock
import time
import tempfile
import unittest

from my_bittrex import volume
from my_bittrex.test import test_utils


class TestMarket(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def setUp(self, mocked_get_market_summaries):
        mocked_get_market_summaries.return_value = fake_get_summaries()
        self.market = volume.Market()

    def test_summaries(self):
        df = self.market._summaries
        self.assertItemsEqual(df.shape, (4, 15))

    def test_currency_value(self):
        market = self.market
        cost = market.currency_value(['XXX', 'XXX'])
        self.assertAlmostEqual(cost, 1, 3)

        cost = market.currency_value(['BBB', 'AAA'])
        self.assertAlmostEqual(cost, 0.1, 3)

        cost = market.currency_value(['AAA', 'BBB'])
        self.assertAlmostEqual(cost, 10, 3)

        cost = market.currency_value(['BBB', 'AAA', 'USDT'])
        self.assertAlmostEqual(cost, 0.2, 3)

        cost = market.currency_value(['CCC', 'AAA'])
        self.assertAlmostEqual(cost, 0.01, 3)

        cost = market.currency_value(['CCC', 'AAA', 'USDT'])
        self.assertEqual(cost, 0.02)

        cost = market.currency_value(['CCC', 'BBB', 'AAA'])
        self.assertAlmostEqual(cost, 0.01, 3)

        cost = market.currency_value(['CCC', 'BBB', 'AAA', 'USDT'])
        self.assertAlmostEqual(cost, 0.02)

        cost = market.currency_value(['AAA', 'BBB', 'CCC'])
        self.assertAlmostEqual(cost, 100, 3)

        cost = market.currency_value(['AAA', 'CCC'])
        self.assertAlmostEqual(cost, 100, 3)

        cost = market.currency_value(['AAA', 'USDT'])
        self.assertAlmostEqual(cost, 2, 3)

        cost = market.currency_value(['USDT', 'AAA'])
        self.assertAlmostEqual(cost, 0.5, 3)

        cost = market.currency_value(['AAA', 'DDD'])
        self.assertEqual(cost, 0)


    @mock.patch('my_bittrex.volume.client.get_currencies')
    def test_currency_volume_1(self, mocked_get_currencies):
        mocked_get_currencies.return_value = fake_get_currencies()

        volume = self.market.currency_volume('AAA', 'USDT', ['USDT'])
        self.assertEqual(volume, 2)

    @mock.patch('my_bittrex.volume.client.get_currencies')
    def test_currency_volume_2(self, mocked_get_currencies):
        mocked_get_currencies.return_value = fake_get_currencies()

        volume = self.market.currency_volume('BBB', 'AAA', ['AAA'])
        self.assertEqual(volume, 1)

    @mock.patch('my_bittrex.volume.client.get_currencies')
    def test_currency_volume_3(self, mocked_get_currencies):
        mocked_get_currencies.return_value = fake_get_currencies()

        volume = self.market.currency_volume('BBB', 'USDT', ['AAA'])
        self.assertEqual(volume, 2)

    @mock.patch('my_bittrex.volume.client.get_currencies')
    def test_usd_volumes(self, mocked_get_currencies):
        mocked_get_currencies.return_value = fake_get_currencies()
        volume_df = self.market.usd_volumes('USDT', ['USDT', 'AAA'])
        computed = volume_df['USDT Volume']
        print computed
        expected = [2.0] * 3
        print expected
        self.assertItemsEqual(computed, expected)

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_caching(self, mocked_get_summaries):
        """
        Test that caching works, and volume.get_summaries() gets called
        only once
        """
        mocked_get_summaries.return_value = fake_get_summaries()
        for i in range(10):
            self.market.summaries()
        mocked_get_summaries.assert_called_once()

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_caching_2(self, mocked_get_summaries):
        """
        Test that caching works, and volume.get_summaries() gets called
        twice if 'cache_timeout_sec' elapses in between calls
        """
        mocked_get_summaries.return_value = fake_get_summaries()
        market = volume.Market(0.1)
        market.summaries()
        time.sleep(.2)
        market.summaries()
        mocked_get_summaries.assert_called_once()
        #raise ValueError('this test should faile, method is called twice')


class TestPortfolio(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_market_summaries')#, return_value=fake_get_summaries())
    @mock.patch('my_bittrex.volume.client.get_balances')#, return_value=fake_get_balances())
    def setUp(self, mocked_get_balances, mocked_get_market_summaries):
        mocked_get_market_summaries.return_value = fake_get_summaries()
        mocked_get_balances.return_value = fake_get_balances()
        self.market = volume.Market()
        self.portfolio = volume.Portfolio()

    def test_value(self):
        self.assertAlmostEqual(self.portfolio.value(self.market, ['AAA', 'AAA']), 3, 3)
        self.assertAlmostEqual(self.portfolio.value(self.market, ['AAA', 'USDT']), 6, 3)


class TestRebalance1(unittest.TestCase):

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test1(self, mocked_market):
        mocked_market.side_effect = [market1(), market2()]
        market = volume.Market()
        print market._summaries

        import pudb
        pudb.set_trace()
        portfolio = volume.start_new_portfolio(market, [1, 1], 'BTC', 2000)
        #print portfolio.portfolio



def market1():
    l = [('USDT-BTC', 1000, 1), ('USDT-ETH', 1000, 1), ('BTC-ETH', 1, 1)]
    return json.loads(test_utils.fake_market(l))

def market2():
    l = [('USDT-BTC', 2000, 1), ('USDT-ETH', 500, 1), ('BTC-ETH', 4, 1)]
    return json.loads(test_utils.fake_market(l))

def fake_get_summaries():
    """
    Fake a summary as would be returned by bittrex.client. Each element in the input list is a tuple of the form
    (market_name, last_price, BaseVolume)
    :return: 
    """
    l = [
        ("AAA-BBB", 0.1, 1),
        ("AAA-CCC", 0.01, 1),
        ("BBB-CCC", 0.1, 2),
        ("USDT-AAA", 2.0, 2)
    ]
    as_dict = json.loads(test_utils.fake_market(l))
    return as_dict


def fake_get_balances():
    """
    Fake a balance with 3 currencies. Prices are not included in balance but to help keep things streight
    prices are:
    AAA:    2
    BBB:    0.2
    CCC:    0.02
    :return: 
    """
    l = [('AAA', 1), ('BBB', 10), ('CCC', 100)]
    as_dict = json.loads(test_utils.fake_balance(l))
    return as_dict


def fake_get_currencies():
    l = [('AAA', 'AAA long', .002), ('BBB', 'BBB long', .002), ('CCC', 'CCC long', .002)]
    as_dict = json.loads(test_utils.fake_currencies(l))
    return as_dict


if __name__ == "__main__":
    unittest.main()
