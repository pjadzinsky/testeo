#!/usr/bin/python
import unittest

from portfolio import portfolio
import market


class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.markets = market.Markets(3600, 0)

    def test_from_largest_markets(self):
        market = self.markets.first_market()
        N = 3
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_largest_markes(market, N, base, value)
        print(p.values)

    def test_from_currencies_1(self):
        market = self.markets.first_market()
        currencies = "USDT"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print(p.values)

    def test_from_currencies_2(self):
        market = self.markets.first_market()
        currencies = "BTC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print(p.values)

    def test_from_currencies_3(self):
        market = self.markets.first_market()
        currencies = "BTC,USDT"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print(p.values)

    def test_from_currencies_4(self):
        market = self.markets.first_market()
        currencies = "BTC,ETH,XRP,LTC"
        base = 'USDT'
        value = 10000
        p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        print(p.values)

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
        print(computed)

    def test_ideal_rebalance(self):
        market = self.markets.first_market()
        currencies = "BTC,ETH,XRP"
        base = 'USDT'
        value = 10000
        state, p = portfolio.Portfolio.from_currencies(market, currencies, base, value)

        balance_XRP_0 = p.values.loc['XRP']
        balance_ETH_0 = p.values.loc['ETH']

        # now suppose ETH multiplies in value by 2 and XRP multiplies by 0 (total money is constant)
        # after another round of ideal rebalancing Balance of ETH has to multiply by 0.5 and
        # XRP goes to infinity. Changing the value of BTC is complex because it affects the price of
        # ETH and XRP in USDT under current code
        # THe test in XRP doesn't work as is designed because 0 * inf is NaN
        market.prices_df.loc['BTC-ETH', 'Last'] *= 2
        market.prices_df.loc['BTC-XRP', 'Last'] *= 0

        min_percentage_change = 0
        p.rebalance(market, state, ['BTC'], min_percentage_change)

        balance_XRP_1 = p.values.loc['XRP']
        balance_ETH_1 = p.values.loc['ETH']

        self.assertAlmostEqual(balance_ETH_1, balance_ETH_0 * 0.5 * (1 - portfolio.COMMISION))

    def test_ideal_rebalance2(self):
        market = self.markets.first_market()
        currencies = "BTC,ETH,XRP"
        base = 'USDT'
        value = 10000
        state, p = portfolio.Portfolio.from_currencies(market, currencies, base, value)

        balance_XRP_0 = p.values.loc['XRP']
        balance_ETH_0 = p.values.loc['ETH']
        balance_BTC_0 = p.values.loc['BTC']

        # now suppose one of the currencies multiplies in value by 4, (total money doubles)
        # after one round of ideal rebalancing the amount in USD in each currency has to multiply by 2.
        # The balance in those currencies that didn't change in price has to double and the balance
        # in the currency that multiply by 4 has to be newB, where "oldB * 1 * 2 = newB * 4" ->
        # newB = oldB/2
        # Changing the value of BTC is complex because it affects the price of
        # ETH and XRP in USDT under current code
        market.prices_df.loc['BTC-ETH', 'Last'] *= 4

        min_percentage_change = 0
        p.rebalance(market, state, ['BTC'], min_percentage_change)

        balance_XRP_1 = p.values.loc['XRP']
        balance_ETH_1 = p.values.loc['ETH']
        balance_BTC_1 = p.values.loc['BTC']

        self.assertAlmostEqual(balance_ETH_1, balance_ETH_0 * 0.5 * (1 - portfolio.COMMISION))
        self.assertAlmostEqual(balance_BTC_1, balance_BTC_0 + balance_BTC_0 * 1 * (1 - portfolio.COMMISION))
        self.assertAlmostEqual(balance_XRP_1, balance_XRP_0 + balance_XRP_0 * 1 * (1 - portfolio.COMMISION))

    def test_limit(self):
        market = self.markets.first_market()
        currencies = "BTC,ETH,XRP"
        base = 'USDT'
        value = 10000
        state, p = portfolio.Portfolio.from_currencies(market, currencies, base, value)
        limit = pd.Series({'BTC': 0.005, 'ETH': 0})
        p.limit_to(limit)

        self.assertEqual(p.values.loc['BTC'], 0.005)
        self.assertEqual(p.values.loc['ETH'], 0)


if __name__ == "__main__":
    unittest.main()
