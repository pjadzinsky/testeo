"""
bittrex.client returns balances as a list of dictionaries with:
 Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid

A portfolio is the type and amount of each cryptocurrency held along with some basic operations.
.
There is a desired 'state' and due to fluctuations some currencies will have more (or less) total_value than their
desired target 'state'. We'll rebalance them periodically.
To avoid spending too much in commissions when rebalancing we have a 'threshold' and we only 'rebalance
cryptocurrencies that increased (or decreased) more than 'threshold' (as a percentage) from desired 'state'.
For example is the desired state is 100 and the threshold is 0.1 we'll sell only if the current total_value is at or above
110 (and buy if the current total_value is at or below 90)
To prevent from buying too much of a sinking currency we are going to put bounds on either the price and/or the
quantities (not clear yet). One idea is to compute the ratio between the current balance and the initial balance
per currency and then say that no currency can have a ratio that is N times bigger than the average ratio.
"""
import numpy as np
import pandas as pd

import bittrex_utils
from market import market

COMMISION = 0.25/100

class Portfolio(object):
    """
    """
    def __init__(self, dataframe):
        """
        Read portfolio from API
        """
        self.dataframe = dataframe

    @classmethod
    def from_largest_markes(cls, market, N, base, value):
        state = cls._uniform_state(market, N, include_usd=False)
        p = cls._start_portfolio(market, state, base, value)
        return state, p

    @classmethod
    def from_currencies(cls, market, currencies, base, value):
        currencies = currencies.split(',')
        weights = 1.0 / len(currencies)
        state = pd.DataFrame({'Weight': weights}, index=currencies)
        p = cls._start_portfolio(market, state, base, value)
        return state, p

    @staticmethod
    def _start_portfolio(market, state, base, value):
        """
        We first start a portfolio that has just 'value' in 'base' and then execute ideal_rebalance on it
        :param market: 
        :param state: 
        :param base: 
        :param value: 
        :return: 
        """
        intermediate_currencies = ['BTC']
        dataframe = pd.DataFrame({'Balance': value, 'Available': value, 'Pending': 0}, index=[base])
        portfolio = Portfolio(dataframe=dataframe)
        portfolio.rebalance(market, state, intermediate_currencies, 0)

        return portfolio

    @staticmethod
    def _uniform_state(market, N, include_usd=True, intermediates=['BTC', 'ETH']):
        """
        
        :param market: DataFrame with market conditions. The 'N' currencies with the most volume will be used to define a
            state
        :param N: number of cryptocurrencies to include
        :param currencies: dict linking currencies to the values of the 'state'
        :param include_usd: If true, usd will be added to the list of cryptocurrencies to hold (even though it is not).
        :return: Dataframe with the weight of each currency (1/N)
        """
        volumes_df = market.usd_volumes(intermediates)
        volumes_df.drop('USDT', axis=0, inplace=True)

        currencies = volumes_df.head(N).index.tolist()
        assert 'USDT' not in volumes_df.index
        if include_usd:
            currencies[-1] = 'USDT'

        state = pd.DataFrame([1. / N] * N, index=currencies, columns=['Weight'])

        return state

    def total_value(self, market, intermediate_currencies):
        """
        Compute the total amount of the portfolio
        param: intermediate_currendcies: list of str
            for each currency in self.dataframe.index 
            intermdiate_currencies + [currency] has to be a valid currency chain
            [A, B, C] (c trades with B and B trades with A and A is the base price to return in)
        """
        return self.value_per_currency(market, intermediate_currencies).sum()

    def value_per_currency(self, market, intermediate_currencies):
        portfolio = self.dataframe

        return portfolio.apply(lambda x: market.currency_chain_value(intermediate_currencies + [x.name]) * x['Balance'],
                               axis=1)
    def ideal_rebalance(self, market, state, intermediate_currencies = ['BTC']):
        """
        Given market, state and intermediate_currencies return the amount to buy (+) or sell (-) for each currency
        to achieve perfect balance.
        
        At this point we don't look at trading costs, sinking currencies, etc
        
        returned dataframe has columns:
        target_usdt:    the value in USD we should have in each currency after rebalancing
        target_currency:    the ideal amount of each currency that achieves this ideal rebalancing
        Buy:            the amount of currency that we have to buy (if > 0) or sell (if < 0) to obtain
                        target_currency
        Buy (USDT):     Amount of USDT needed for the transaction (not taking transactions costs into accoun)
        intermediate_currencies: ?
        """
        total_value = self.total_value(market, ['USDT', 'BTC'])

        buy_df = pd.merge(self.dataframe, state, left_index=True, right_index=True, how='outer')      # if state has new cryptocurrencies there will be NaNs
        buy_df.fillna(0, inplace=True)

        buy_df.loc[:, 'target_usdt'] = buy_df['Weight'] * total_value
        buy_df.loc[:, 'currency_in_usdt'] = buy_df.apply(
            lambda x: market.currency_chain_value(['USDT'] + intermediate_currencies + [x.name]), axis=1)
        buy_df.loc[:, 'target_currency'] = buy_df['target_usdt'] / buy_df['currency_in_usdt']

        buy_df.loc[:, 'Buy'] = buy_df['target_currency'] - buy_df['Balance']
        buy_df.loc[:, 'Buy (USDT)'] = buy_df.apply(
            lambda x: x.Buy * market.currency_chain_value(['USDT'] + intermediate_currencies + [x.name]),
            axis=1
        )

        return buy_df

    def rebalance(self, market, state, intermediate_currencies, min_percentage_change):
        """
        Given a state, buy/sell positions to approximate target_portfolio
        
        base_currency:  base currency to do computations
        threshold:  currencies are only balanced if difference with target is above/below this threshold (express
                    as a percentage)
        """
        buy_df = self.ideal_rebalance(market, state, intermediate_currencies)
        # apply transaction costs
        buy_df.loc[:, 'Buy'] = buy_df['Buy'].apply(apply_transaction_cost)

        # we only buy/sell is movement is above 'min_percentage_change'. However, this movement could be in the
        # amount of cryptocurrency we own (by_currency=True) or in the USDT it represents (by_currency=False)
        by_currency = True
        for currency in buy_df.index:
            if by_currency:
                # if 'buy_df['Buy'] represents less than 'min_percentage_change' from 'position' don't do anything
                percentage_change = np.abs(buy_df.loc[currency, 'Buy']) / buy_df.loc[currency, 'Balance']
            else:
                # if 'buy_df['Buy (USDT)'] represents less than 'min_percentage_change' from 'position' don't do anything
                percentage_change = np.abs(buy_df.loc[currency, 'Buy (USDT)']) / buy_df.loc[currency, 'target_usdt']
            buy_df.loc[currency, "change"] = percentage_change
            if percentage_change < min_percentage_change:
                buy_df.loc[currency, 'Buy'] = 0

        # if 'USDT' is in self.dataframe, remove it. Each transaction is simulated against 'USDT' but we don't
        # buy/sell 'USDT' directly. Not doing this will lead to problems and double counting
        if 'USDT' in buy_df.index:
            buy_df.loc['USDT', 'Buy'] = 0
            buy_df.loc['USDT', 'Buy (USDT)'] = 0

        self.mock_buy(buy_df[['Buy', 'Buy (USDT)', 'change']])

    def mock_buy(self, buy_df):
        """
        This is a method that mocks sending a buy/sell order to the client and its execution.
        After this method executes, we'll assume that we buy/sell whatever we requested at the requested prices
        
        I don't understand if bittrex client talks in usdt, base or currency when placing orders. I'm just
        mocking the result here, not the call
        
        :param buy_df: 
        :return: 
        """

        # There is 0.25% cost on each buy/sell transaction. Although exchanging ETH for BTC shows as two transactions
        # in 'buy' and should pay 0.25% only once, most transactions in 'buy' should pay the 0.25%. I'm going to
        # overestimate the transaction cost by paying the 0.25% for every transaction in buy
        # when we want to buy X, we end up with x * (1 - cost)
        # when we want to sell X, we end up with x * (1 - cost) base. I'm modeling this as we actuall sold
        # x * (1 + cost)

        # the 'index' in buy_df might not be the same as in self.dataframe. That's why we start merging based on
        # index and we use 'outer'.
        self.dataframe = pd.merge(self.dataframe, buy_df, left_index=True, right_index=True, how='outer')
        #  If new values are added to index there will be NaN
        self.dataframe.fillna(0, inplace=True)
        self.dataframe['Balance'] += self.dataframe['Buy']
        self.dataframe['Available'] += self.dataframe['Buy']

        self.dataframe.loc['USDT', 'Balance'] -= self.dataframe['Buy (USDT)'].sum()
        self.dataframe.loc['USDT', 'Available'] -= self.dataframe['Buy (USDT)'].sum()
        self.dataframe.drop(['Buy', 'Buy (USDT)', 'change'], inplace=True, axis=1)


def apply_transaction_cost(buy):
    """ buy is a float, the amount of either currency or dollars to buy (if positive) or sell (if negative)
    """
    try:
        buy *= 1.0
    except:
        raise IOError('buy should be numeric')

    if buy > 0:
        buy -= buy * COMMISION
    else:
        buy += buy * COMMISION

    return buy

