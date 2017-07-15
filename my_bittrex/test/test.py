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

    def test_cost_in_base_currency(self):
        market = self.market
        cost = market.currency_value(['XXX', 'XXX'])
        self.assertAlmostEqual(cost, 1, 3)

        cost = market.currency_value(['BBB', 'AAA'])
        self.assertAlmostEqual(cost, 0.1, 3)

        cost = market.currency_value(['AAA', 'BBB'])
        self.assertAlmostEqual(cost, 10, 3)

        cost = market.currency_value(['CCC', 'AAA'])
        self.assertAlmostEqual(cost, 0.01, 3)

        cost = market.currency_value(['CCC', 'BBB', 'AAA'])
        self.assertAlmostEqual(cost, 0.01, 3)

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
        expected = [2.0] * 3
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
        print 1
        market.summaries()
        time.sleep(.2)
        print 2
        market.summaries()
        mocked_get_summaries.assert_called_once()
        #raise ValueError('this test should faile, method is called twice')
'''

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
        self.market = volume.Market()
        self.portfolio = volume.Portfolio()

    def test_currency_value_1(self):
        value = self.portfolio.currency_value(self.market, ['AAA', 'AAA'])
        self.assertEqual(value, 1)

    def test_currency_value_2(self):
        value = self.portfolio.currency_value(self.market, ['AAA', 'USDT'])
        self.assertEqual(value, 2)

    def test_currency_value_3(self):
        value = self.portfolio.currency_value(self.market, ['BBB', 'AAA', 'USDT'])
        self.assertEqual(value, 2)

    def test_currency_value_3(self):
        value = self.portfolio.currency_value(self.market, ['CCC', 'AAA', 'USDT'])
        self.assertEqual(value, 2)

    def test_currency_value_4(self):
        value = self.portfolio.currency_value(self.market, ['CCC', 'BBB', 'AAA', 'USDT'])
        self.assertEqual(value, 2)

    def test_value(self):
        import pudb
        pudb.set_trace()
        self.assertAlmostEqual(self.portfolio.value(self.market, 'AAA'), 3, 3)
        self.assertAlmostEqual(self.portfolio.value(self.market, 'USDT'), 6, 3)

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
                "MarketName" : "BBB-CCC",
                "High" : 0.1,
                "Low" : 0.1,
                "Volume" : 1,
                "Last" : 0.1,
                "BaseVolume" : 2,
                "TimeStamp" : "2014-07-09T07:21:40.51",
                "Bid" : 0.1,
                "Ask" : 0.1,
                "OpenBuyOrders" : 18,
                "OpenSellOrders" : 18,
                "PrevDay" : 0.1,
                "Created" : "2014-05-30T07:57:49.637",
                "DisplayMarketName" : null
            }, {
                "MarketName" : "USDT-AAA",
                "High" : 2,
                "Low" : 2,
                "Volume" : 1,
                "Last" : 2,
                "BaseVolume" : 2,
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


def fake_get_currencies():
    response = """{
        "success" : true,
        "message" : "",
        "result" : [{
            "Notice": null,
            "TxFee": 0.002,
            "CurrencyLong": "AAA long",
            "CoinType": "BITCOIN",
            "Currency": "AAA",
            "MinConfirmation": 6,
            "BaseAddress": "LhyLNfBkoKshT7R8Pce6vkB9T2cP2o84hx",
            "IsActive": true
        }, {
            "Notice": null,
            "TxFee": 0.002,
            "CurrencyLong": "BBB long",
            "CoinType": "BITCOIN",
            "Currency": "BBB",
            "MinConfirmation": 6,
            "BaseAddress": "LhyLNfBkoKshT7R8Pce6vkB9T2cP2o84hx",
            "IsActive": true
        }, {
            "Notice": null,
            "TxFee": 0.002,
            "CurrencyLong": "CCC long",
            "CoinType": "BITCOIN",
            "Currency": "CCC",
            "MinConfirmation": 6,
            "BaseAddress": "LhyLNfBkoKshT7R8Pce6vkB9T2cP2o84hx",
            "IsActive": true
        } ]
    } """
    return json.loads(response)


if __name__ == "__main__":
    unittest.main()
