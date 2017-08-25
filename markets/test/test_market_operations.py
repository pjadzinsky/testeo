#!/usr/bin/python
import unittest
import time

import pandas as pd
import mock

from markets import market_operations
from markets import recreate_markets


def currencies_df():
    values = [None] * 6
    names = ['USDT', 'AAA', 'BBB', 'CCC', 'XXX', 'YYY']
    return pd.DataFrame(values, index=names)


class TestRecreateMarkets(unittest.TestCase):
    def test1(self):
        hours = 1
        offset = 0
        markets = recreate_markets.Markets(hours, offset)

        import pudb
        pudb.set_trace()
        first_market = markets.next()
        self.assertItemsEqual(first_market.shape, (261, 3))


class TestMarketOperations(unittest.TestCase):
    def setUp(self):
        last = [1, 10, 20]
        BaseVolume = [1, 1, 1]
        Volume = [10, 10, 10]

        self.market = pd.DataFrame({'last': last, 'BaseVolume': BaseVolume, 'Volume': Volume},
                                   index=['USDT-A', 'A-B', 'A-C'])

    def test_currency_chain_value(self):
        computed = market_operations.volume(self.market, ['A', 'USDT'])
        expected = 1 * 1 + 10 * 1 * 10 + 20 * 1 * 1


class TestMarket(unittest.TestCase):
    def setUp(self):
        time = 10
        names = ['USDT-AAA', 'AAA-BBB', 'AAA-CCC']
        last = [2, 10, 0.1]
        volume = [100, 200, 300]
        names += ['USDT-XXX', 'XXX-BBB']
        last += [.1, 2]
        volume += [10, 100]

        df = fake_short_s3_key(names, last, volume)
        self.market = recreate_markets.Market(time, df)

    def test_caching(self):

        recreate_markets.Market.from_s3_key('1502981286_short')
        t0 = time.time()
        recreate_markets.Market.from_s3_key('1502981286_short')
        t1 = time.time()
        recreate_markets.Market.from_s3_key('1502981286_short')
        t2 = time.time()
        self.assertLess(t1 - t0, 1E-3)
        self.assertLess(t2 - t1, 1E-3)

    def test_currency_chain_value(self):
        self.assertEqual(self.market.currency_chain_value(['USDT']), 1)
        self.assertEqual(self.market.currency_chain_value(['AAA']), 1)
        self.assertEqual(self.market.currency_chain_value(['USDT', 'AAA']), 2)
        self.assertEqual(self.market.currency_chain_value(['AAA', 'BBB']), 10)
        self.assertEqual(self.market.currency_chain_value(['USDT', 'AAA', 'BBB']), 20)
        self.assertEqual(self.market.currency_chain_value(['AAA', 'CCC']), 0.1)
        self.assertEqual(self.market.currency_chain_value(['USDT', 'AAA', 'CCC']), 0.2)
        self.assertEqual(self.market.currency_chain_value(['CCC', 'AAA', 'CCC']), 1)
        self.assertEqual(self.market.currency_chain_value(['CCC', 'AAA', 'USDT', 'XXX', 'BBB', 'XXX', 'USDT', 'AAA', 'CCC']), 1)

    def test__market_name(self):
        computed = self.market._market_name('a', 'b')
        self.assertEqual(computed, 'a-b')

    def test_currency_chain_volume(self):
        self.assertEqual(self.market.currency_chain_volume([]), 0)
        self.assertEqual(self.market.currency_chain_volume(['ABC']), 0)
        self.assertEqual(self.market.currency_chain_volume(['USDT', 'ABC']), 0)
        computed = self.market.currency_chain_volume([])
        self.assertEqual(computed, 0)
        computed = self.market.currency_chain_volume(['AAA'])
        self.assertEqual(computed, 0)
        computed = self.market.currency_chain_volume(['USDT', 'ABC'])
        self.assertEqual(computed, 0)
        computed = self.market.currency_chain_volume(['USDT', 'AAA'])
        self.assertEqual(computed, 200)
        computed = self.market.currency_chain_volume(['USDT', 'AAA', 'BBB'])
        self.assertEqual(computed, 4000)
        computed = self.market.currency_chain_volume(['BBB', 'AAA', 'USDT'])
        self.assertEqual(computed, 10)
        computed = self.market.currency_chain_volume(['BBB', 'AAA', 'BBB'])
        self.assertEqual(computed, 200)
        computed = self.market.currency_chain_volume(['CCC', 'AAA', 'CCC'])
        self.assertEqual(computed, 300)
        computed = self.market.currency_chain_volume(['CCC', 'AAA', 'USDT', 'XXX', 'BBB', 'XXX', 'USDT', 'AAA', 'CCC'])
        self.assertEqual(computed, 300)


    @mock.patch('bittrex_utils.currencies_df', return_value=currencies_df())
    def test__direct_volume_in_base(self, mocked_currencies):

        computed = self.market._direct_volume_in_base(base='USDT', currency='AAA')
        self.assertEqual(computed, 200)
        computed = self.market._direct_volume_in_base(base='AAA', currency='USDT')
        self.assertEqual(computed, 100)
        computed = self.market._direct_volume_in_base(base='USDT', currency='BBB')
        self.assertEqual(computed, 0)
        computed = self.market._direct_volume_in_base(base='CCC', currency='AAA')
        self.assertEqual(computed, 300)
        computed = self.market._direct_volume_in_base(base='AAA', currency='CCC')
        self.assertEqual(computed, 30)

    @mock.patch('bittrex_utils.currencies_df', return_value=currencies_df())
    def test_currency_volume(self, mocked_currencies):

        computed = self.market.currency_volume('USDT', [[]])
        self.assertEqual(computed, 201)
        computed = self.market.currency_volume('USDT', [['AAA']])
        self.assertEqual(computed, 200)
        computed = self.market.currency_volume('USDT', [['XXX']])
        self.assertEqual(computed, 1)
        computed = self.market.currency_volume('USDT', [['AAA'], ['USDT']])
        self.assertEqual(computed, 200)
        computed = self.market.currency_volume('USDT', [['XXX'], ['USDT']])
        self.assertEqual(computed, 1)
        computed = self.market.currency_volume('USDT', [['BBB'], ['AAA']])
        self.assertEqual(computed, 0)
        computed = self.market.currency_volume('USDT', [['AAA'], ['BBB']])
        self.assertEqual(computed, 4000)
        computed = self.market.currency_volume('USDT', [['XXX'], ['BBB']])
        self.assertEqual(computed, 20)
        computed = self.market.currency_volume('USDT', [['AAA', 'XXX'], ['BBB']])
        self.assertEqual(computed, 4020)

    @mock.patch('bittrex_utils.currencies_df', return_value=currencies_df())
    def test_usd_volumes(self, mocked_currencies):
        values = [None] * 4
        names = ['USDT', 'AAA', 'BBB', 'CCC']
        mocked_currencies.return_value = pd.DataFrame(values, index=names)

        computed = self.market.usd_volumes()



def fake_market(currency_prices_vols):
    """ Return a jsong blob as would be returned by bittrex.client.get_market_summaries
    but where the currencies, prices, volues are the tuples in currency_prices_vols
    """
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
    """

    template = """
            "MarketName" : "{0}",
            "High" : {1},
            "Low" : {1},
            "Volume" : {2},
            "Last" : {1},
            "BaseVolume" : {3},
            "TimeStamp" : "2014-07-09T07:19:30.15",
            "Bid" : {1},
            "Ask" : {1},
            "OpenBuyOrders" : 15,
            "OpenSellOrders" : 15,
            "PrevDay" : {1},
            "Created" : "2014-03-20T06:00:00",
            "DisplayMarketName" : null
     """
    response += '}, {'.join([template.format(c, b, v, v*b) for c, b, v in currency_prices_vols])
    response += '}]}'

    return response


def fake_short_s3_key(names, last, volume):
    """
    files in s3 of the type <timestamp_short.csv> have csvs indexed by MarketName with columns
    'Last', 'Volume' and 'BaseVolume'
    
    :param names: 
    :param last: 
    :param volume: 
    :return:  df as would be obtained by doing Market.from_s3_key(s3_key)
    """
    df = pd.DataFrame({'Last': last, 'Volume': volume}, index=names)

    df.loc[:, 'BaseVolume'] = df.apply(lambda x: x.Last * x.Volume, axis=1)

    return df


if __name__ == "__main__":
    unittest.main()
