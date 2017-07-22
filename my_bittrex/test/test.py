#!/usr/bin/python

import json
import mock
import time
import tempfile
import unittest

from my_bittrex import volume
from my_bittrex.test import test_utils


class TestMarket(unittest.TestCase):
    def setUp(self):
        self.market = volume.Market(json_blob=market0())

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

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_direct_volume_in_base(self, mocked_market):
        """
        l = [('USDT-BTC', 1000, 1), ('USDT-ETH', 1000, 1), ('BTC-ETH', 1, 1)]
        """
        market = volume.Market(json_blob=market1())
        computed = market._direct_volume_in_base('BTC', 'BTC')
        self.assertEqual(computed, 0)

        computed = market._direct_volume_in_base('BTC', 'XXX')
        self.assertEqual(computed, 0)

        computed = market._direct_volume_in_base('BTC', 'USDT')
        self.assertEqual(computed, 1)

        computed = market._direct_volume_in_base('USDT', 'BTC')
        self.assertEqual(computed, 1000)

        computed = market._direct_volume_in_base('ETH', 'BTC')
        self.assertEqual(computed, 1)

        computed = market._direct_volume_in_base('BTC', 'ETH')
        self.assertEqual(computed, 1)

        computed = market._direct_volume_in_base('ETH', 'USDT')
        self.assertEqual(computed, 1)

        computed = market._direct_volume_in_base('USDT', 'ETH')
        self.assertEqual(computed, 1000)

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_direct_volume_in_base2(self, mocked_market):
        # Market is: [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
        market = volume.Market(json_blob=market2())
        import pudb
        pudb.set_trace()
        computed = market._direct_volume_in_base('BTC', 'USDT')
        self.assertEqual(computed, 10)

        computed = market._direct_volume_in_base('USDT', 'BTC')
        self.assertEqual(computed, 20000)

        computed = market._direct_volume_in_base('ETH', 'BTC')
        self.assertEqual(computed, 10)

        computed = market._direct_volume_in_base('BTC', 'ETH')
        self.assertEqual(computed, 2.5)

        computed = market._direct_volume_in_base('ETH', 'USDT')
        self.assertEqual(computed, 10)

        computed = market._direct_volume_in_base('USDT', 'ETH')
        self.assertEqual(computed, 5000)

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

    @mock.patch('my_bittrex.volume.client.get_currencies')
    def test_volumes(self, mocked_get_currencies):
        mocked_get_currencies.return_value = fake_get_currencies()
        volume_df = self.market.usd_volumes('USDT', ['AAA', 'USDT'])
        print volume_df
        #computed = volume_df['USDT Volume']

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_caching(self, mocked_get_summaries):
        """
        Test that caching works, and volume.get_summaries() gets called
        only once
        """
        mocked_get_summaries.return_value = market1()
        market = volume.Market()
        for i in range(10):
            market.summaries()
        mocked_get_summaries.assert_called_once()

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_caching_2(self, mocked_get_summaries):
        """
        Test that caching works, and volume.get_summaries() gets called
        twice if 'cache_timeout_sec' elapses in between calls
        """
        mocked_get_summaries.return_value = market1()
        market = volume.Market(0.1)
        market.summaries()
        time.sleep(.2)
        market.summaries()
        mocked_get_summaries.assert_called_once()


class TestPortfolio(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_balances')#, return_value=fake_get_balances())
    def setUp(self, mocked_get_balances):
        mocked_get_balances.return_value = fake_get_balances()
        self.market = volume.Market(json_blob=market0())
        self.portfolio = volume.Portfolio()

    def test_value(self):
        self.assertAlmostEqual(self.portfolio.value(self.market, ['AAA', 'AAA']), 3, 3)
        self.assertAlmostEqual(self.portfolio.value(self.market, ['AAA', 'USDT']), 6, 3)


class TestRebalance1(unittest.TestCase):

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test1(self, mocked_market):
        """ start_new_portfolio will call get_currencies, we could mock it but there is not need for it as long
        as we use currencies that do exist for real (unlike 'AAA')"""
        mocked_market.side_effect = [market2()]
        market = volume.Market(json_blob=market1())
        print market._summaries

        portfolio = volume.start_new_portfolio(market, [1, 1], 'BTC', 2000)

        print portfolio.portfolio



def market1():
    l = [('USDT-BTC', 1000, 1), ('USDT-ETH', 1000, 1), ('BTC-ETH', 1, 1)]
    return test_utils.fake_market(l)


def market2():
    l = [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
    return test_utils.fake_market(l)


def market0():
    """
    Fake a summary as would be returned by bittrex.client. Each element in the input list is a tuple of the form
    (market_name, last_price, Volume)
    :return: 
    """
    l = [
        ("AAA-BBB", 0.1, 10),
        ("AAA-CCC", 0.01, 100),
        ("BBB-CCC", 0.1, 20),
        ("USDT-AAA", 2.0, 2)
    ]
    return test_utils.fake_market(l)

def market_real1():
    """
    Ask                                  2795
    BaseVolume                    2.79336e+07
    Bid                               2785.14
    Created           2015-12-11T06:31:40.633
    High                                 2930
    Last                              2785.14
    Low                                  2280
    OpenBuyOrders                        3082
    OpenSellOrders                        661 
    PrevDay                              2305
    TimeStamp          2017-07-21T06:55:04.12
    Volume                            10562.9
    Base                                 USDT
    Currency                              BTC
    
    in ipython running:
    json.loads(test.market_real1()) matches the above dictionary to a reasonable precission
    """
    l = [("USDT-BTC", 2785, 10562)]
    return test_utils.fake_market(l)


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
