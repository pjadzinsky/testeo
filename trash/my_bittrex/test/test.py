#!/usr/bin/python

import json
import time
import unittest

import mock
import pandas as pd

from trash.my_bittrex import test_utils
from trash.my_bittrex import volume


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

    def test__volume_in_usdt_1(self):
        # Market is: [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
        market = volume.Market(json_blob=market2())
        computed = market._volume_in_usdt('ETH')
        expected = 10 * 500 + 10 * 500
        self.assertEqual(computed, expected)

    def test__volume_in_btc_1(self):
        # Market is: [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
        market = volume.Market(json_blob=market2())
        computed = market._volume_in_btc('ETH')
        expected = 10 * 0.25 + 10 * 500 / 2000.0
        self.assertEqual(computed, expected)

    def test__volume_in_eth_1(self):
        # Market is: [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
        market = volume.Market(json_blob=market2())
        computed = market._volume_in_eth('USDT')
        expected = 10 + 10 * 2000 / 500.0
        self.assertEqual(computed, expected)

    def test_currency_volume_in_base_raises(self):
        market = volume.Market(json_blob=market2())
        self.assertRaises(AssertionError, market.currency_volume_in_base, 'XXX', 'BTC')

    def test_currency_volume_in_base_1(self):
        # Market is: [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
        market = volume.Market(json_blob=market2())
        computed = market.currency_volume_in_base('USDT', 'BTC')
        expected = 10 * 2000 + 10 * .25 * 2000
        self.assertEqual(computed, expected)

    def test_usd_volumes(self):
        # Market is: [('USDT-BTC', 1000, 1), ('USDT-ETH', 1000, 1), ('BTC-ETH', 1, 1)]
        market = volume.Market(json_blob=market1())

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
        self.assertAlmostEqual(self.portfolio.total_value(self.market, ['AAA', 'AAA']), 3, 3)
        self.assertAlmostEqual(self.portfolio.total_value(self.market, ['AAA', 'USDT']), 6, 3)

    def test_empty_init(self):
        portfolio = volume.Portfolio()
        self.assertItemsEqual(portfolio.portfolio.columns, ['Balance', 'Available', 'Pending', 'CryptoAddress',
                                                            'Requested', 'Uuid'])
        self.assertEqual(portfolio.portfolio.index.name, 'Currency')
        self.assertTrue(portfolio.portfolio.empty)

    @mock.patch('my_bittrex.volume.client.get_balances')
    def test_value_per_currency(self, mocked_get_balances):
        """
        balance1 is: [('BTC', 2), ('ETH', 3), ('USDT', 4)]
        market2 is: [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
        
        :param mocked_get_balances: 
        :return: 
        """
        mocked_get_balances.return_value = balance1()
        market = volume.Market(json_blob=market2())

        portfolio = volume.Portfolio()
        computed = portfolio.value_per_currency(market, ['BTC', 'USDT'])
        self.assertEqual(type(computed), pd.Series)
        self.assertItemsEqual(computed.tolist(), [4000, 1500, 4])

        computed = portfolio.value_per_currency(market, ['ETH', 'USDT'])
        self.assertItemsEqual(computed.tolist(), [4000, 1500, 4])


    def test_start_portfolio(self):
        market = volume.Market(json_blob=market1())
        state = volume.define_state(market, 2, include_usd=False)
        portfolio = volume.Portfolio()
        portfolio.start_portfolio(market, state, 'USDT', 1000)
        # we are overestimating the cost of the transaction because we are counting 4 transactions instead of 2
        # to establish the portfolio (selling USDT to buy BTC pays only once and I'm counting it twice, same for
        # ETH)
        self.assertEqual(portfolio.total_value(market, ['USDT']), 995)
        # 0.5 * (1 - 0.25%/100) = 0.49875
        # buy selling all 1000 dollars, due to a fake commission I end up with a -2.5 balance
        self.assertItemsEqual(portfolio.portfolio['Balance'], [.49875, .49875, -2.5])


class TestApplyTransactionCost(unittest.TestCase):
    def test_sell(self):
        computed = volume.apply_transaction_cost(-100)
        expected = -100.25
        self.assertEqual(computed, expected)

    def test_buy(self):
        computed = volume.apply_transaction_cost(100)
        expected = 99.75
        self.assertEqual(computed, expected)


class TestState(unittest.TestCase):
    def test_uniform(self):
        """
        [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10), ('BTC-AAA', 1E-5, 1000),
         ('BTC-BBB', 1E-3, 1E6)]
        
        :return: 
        """
        market = volume.Market(json_blob=market3())
        state = volume.define_state(market, 4)
        self.assertEqual(state.shape, (4, 1))
        self.assertItemsEqual(state['Weight'], [0.25] * 4)


class TestRebalance1(unittest.TestCase):

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_from_empty_balance(self, mocked_market):
        """ start_new_portfolio will call get_currencies, we could mock it but there is not need for it as long
        as we use currencies that do exist for real (unlike 'AAA')
        
        """
        mocked_market.return_value = market1()
        market = volume.Market()
        state = volume.define_state(market, 2, include_usd=False)
        portfolio = volume.Portfolio()
        portfolio.ideal_rebalance(market, state)

        """
        time.sleep(.1)
        print(market.summaries())

        # Now we have 2500 , after rebalancing there should 1250 in each
        # since Market2 is [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
        # 'BTC' @ 2000, position should be 1250/2000 = 0.625
        # 'ETH' @ 500, position should be 1250/500 = 2.5
        portfolio.rebalance(market, state, portfolio, 'USDT', 0)
        print(portfolio.portfolio)
        """


def market1():
    l = [('USDT-BTC', 1000, 1), ('USDT-ETH', 1000, 1), ('BTC-ETH', 1, 1)]
    return test_utils.fake_market(l)


def market2():
    l = [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10)]
    return test_utils.fake_market(l)

def market3():
    l = [('USDT-BTC', 2000, 10), ('USDT-ETH', 500, 10), ('BTC-ETH', 0.25, 10), ('BTC-AAA', 1E-5, 1000),
         ('BTC-BBB', 1E-3, 1E6), ('ETH-CCC', 2, 100)]
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


def balance1():
    l = [('BTC', 2), ('ETH', 3), ('USDT', 4)]
    return json.loads(test_utils.fake_balance(l))

def fake_get_currencies():
    l = [('AAA', 'AAA long', .002), ('BBB', 'BBB long', .002), ('CCC', 'CCC long', .002)]
    as_dict = json.loads(test_utils.fake_currencies(l))
    return as_dict


if __name__ == "__main__":
    unittest.main()
