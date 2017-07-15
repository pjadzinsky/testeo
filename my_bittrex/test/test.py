#!/usr/bin/python

import json
import mock
import time
import tempfile
import unittest

from my_bittrex import volume
from my_bittrex.test import test_utils


class TestClass(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_get_summaries(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()

    @mock.patch('my_bittrex.volume.client.get_balances')
    def test_get_balances(self, mocked_balances):
        mocked_balances.return_value = fake_get_balances()
        print volume.get_portfolio()


class TestMarket(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def setUp(self, mocked_get_market_summaries):
        mocked_get_market_summaries.return_value = fake_get_summaries()
        self.market = volume.Market()

    def test_summaries(self):
        df = self.market._summaries
        self.assertItemsEqual(df.shape, (3, 15))

    def test_cost_in_base_currency(self):
        market = self.market
        cost = market.currency_cost_in_base_currency('XXX', 'XXX')
        self.assertEqual(cost, 1)

        cost = market.currency_cost_in_base_currency('BBB', 'AAA')
        self.assertEqual(cost, 0.1)

        cost = market.currency_cost_in_base_currency('AAA', 'BBB')
        self.assertEqual(cost, 10)

        cost = market.currency_cost_in_base_currency('CCC', 'AAA')
        self.assertEqual(cost, 0.01)

        cost = market.currency_cost_in_base_currency('AAA', 'CCC')
        self.assertEqual(cost, 100)

        cost = market.currency_cost_in_base_currency('AAA', 'USDT')
        self.assertEqual(cost, 2)

        self.assertRaises(ValueError, market.currency_cost_in_base_currency, 'AAA', 'DDD')


'''
    def test_usd_volume(self):
        volume = self.market.usd_volumes()
        self.assertEqual(volume, 2000002)

    def test_caching(self, mocked_get_summaries):
        """
        Test that caching works, and volume.get_summaries() gets called
        only once
        """
        mocked_get_summaries.return_value = fake_get_summaries()
        market = volume.Market(600)
        for i in range(10):
            market.summaries()
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
        raise ValueError('this test should faile, method is called twice')

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_currency_cost_in_base_currency_1(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()
        market = volume.Market()
        computed = market.currency_cost_in_base_currency('XXX', 'XXX')
        expected = 1
        self.assertEqual(computed, expected)

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_currency_cost_in_base_currency_2(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()
        market = volume.Market()
        computed = market.currency_cost_in_base_currency('BTC', 'USDT')
        expected = 2500
        self.assertEqual(computed, expected)

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_currency_cost_in_base_currency_3(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()
        market = volume.Market()
        computed = market.currency_cost_in_base_currency('USDT', 'BTC')
        expected = 1.0 / 2500
        self.assertEqual(computed, expected)

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_currency_cost_in_base_currency_4(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()
        market = volume.Market()
        self.assertRaises(ValueError, market.currency_cost_in_base_currency, 'YYY', 'XXX')
        
'''

class TestPortfolio(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_market_summaries')#, return_value=fake_get_summaries())
    @mock.patch('my_bittrex.volume.client.get_balances')#, return_value=fake_get_balances())
    def setUp(self, mocked_get_balances, mocked_get_market_summaries):
        mocked_get_market_summaries.return_value = fake_get_summaries()
        mocked_get_balances.return_value = fake_get_balances()
        self.portfolio = volume.Portfolio()

    def test_get_portfolio(self):
        print self.portfolio.value('AAA')

'''
    def test_rebalance(self, mocked_balances, mocked_summaries):
        mocked_balances.return_value = fake_get_balances()
        portfolio = volume.Portfolio(state, initial_portfolio, portfolio)
        volume.rebalance()

        print 1

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    @mock.patch('my_bittrex.volume.client.get_balances')
    def test_total(self, mocked_balances, mocked_summaries):
        mocked_balances.return_value = fake_get_balances()
        mocked_summaries.return_value = fake_get_summaries()

        computed = volume.get_total_balance('BTC')
        print computed

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_usd_volume(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()
        computed = volume.get_USD_volume()
        print computed

    @mock.patch('my_bittrex.volume.client.get_portfolio')
    def test_market_names(self, mocked_balances):
        mocked_balances.return_value = fake_get_balances()

        computed = volume._market_names(volume.get_portfolio(), 'ABC')
        expected = ['ABC-' + c for c in ['A3C', 'BTC', 'ETH']]
        self.assertEqual(computed, expected)

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    @mock.patch('my_bittrex.volume.client.get_portfolio')
    def test_start_new_portfolio(self, mocked_balances, mocked_summaries):
        mocked_balances.return_value = fake_get_balances()
        mocked_summaries.return_value = fake_get_summaries()

        csv_file = tempfile.mkstemp()
        import pudb
        pudb.set_trace()
        volume.start_new_portfolio(10, 'BTC', 1, csv_file=csv_file)
        btc_value = volume.get_total_balance('BTC')
        print btc_value
        #self.assertEqual(computed, expected)


    def test_value(self):
        self.assertAlmostEqual(self.portfolio.value('BTC'), 1, 3)

    """
    def test_rebalance(self):
        pass
        #volume.rebalance('BTC')
    """



class TestTestUtils(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_start_new_portfolio(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()
        summary = volume.get_summaries()
        perturbed = test_utils.perturb_market(summary, 0.1)

        joined = perturbed.join(summary, lsuffix='l', rsuffix='r')
        print joined[['Lastl', 'Lastr']]

'''

def fake_get_summaries():
    """
    Fake a summary with 3 currencies. Prices are not included in balance but to help keep things streight
    prices are:
    AAA:    1
    BBB:    0.1
    CCC:    0.01
    :return: 
    """
    print 'faking get summaries'
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
                "MarketName" : "AAA-BBB",
                "High" : 0.1,
                "Low" : 0.1,
                "Volume" : 10,
                "Last" : 0.1,
                "BaseVolume" : 1,
                "TimeStamp" : "2014-07-09T07:19:30.15",
                "Bid" : 0.1,
                "Ask" : 0.1,
                "OpenBuyOrders" : 15,
                "OpenSellOrders" : 15,
                "PrevDay" : 0.1,
                "Created" : "2014-03-20T06:00:00",
                "DisplayMarketName" : null
            }, {
                "MarketName" : "AAA-CCC",
                "High" : 0.01,
                "Low" : 0.01,
                "Volume" : 100,
                "Last" : 0.01,
                "BaseVolume" : 1,
                "TimeStamp" : "2014-07-09T07:21:40.51",
                "Bid" : 0.01,
                "Ask" : 0.01,
                "OpenBuyOrders" : 18,
                "OpenSellOrders" : 18,
                "PrevDay" : 0.01,
                "Created" : "2014-05-30T07:57:49.637",
                "DisplayMarketName" : null
            }, {
                "MarketName" : "USDT-AAA",
                "High" : 2,
                "Low" : 2,
                "Volume" : 2000,
                "Last" : 2,
                "BaseVolume" : 2000000,
                "TimeStamp" : "2014-07-09T07:21:40.51",
                "Bid" : 2,
                "Ask" : 2,
                "OpenBuyOrders" : 18,
                "OpenSellOrders" : 18,
                "PrevDay" : 2,
                "Created" : "2014-05-30T07:57:49.637",
                "DisplayMarketName" : null
            }
        ]
    } """
    return json.loads(response)


def fake_get_balances():
    """
    Fake a balance with 3 currencies. Prices are not included in balance but to help keep things streight
    prices are:
    AAA:    2
    BBB:    0.2
    CCC:    0.02
    :return: 
    """
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
                "Currency" : "AAA",
                "Balance" : 1.0,
                "Available" : 1.0,
                "Pending" : 0.00000000,
                "CryptoAddress" : "DLxcEt3AatMyr2NTatzjsfHNoB9NT62HiF",
                "Requested" : false,
                "Uuid" : null
            }, {
                "Currency" : "BBB",
                "Balance" : 10.0,
                "Available" : 10.0,
                "Pending" : 0.00000000,
                "CryptoAddress" : "1Mrcdr6715hjda34pdXuLqXcju6qgwHA31",
                "Requested" : false,
                "Uuid" : null
            }, {
                "Currency" : "CCC",
                "Balance" : 100.0,
                "Available" : 100.0,
                "Pending" : 0.00000000,
                "CryptoAddress" : "1Mrcdr6715hjda34pdXuLqXcju6qgwHA31",
                "Requested" : false,
                "Uuid" : null
            }
        ]
    } """
    return json.loads(response)


if __name__ == "__main__":
    unittest.main()
