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
import pandas as pd
import bittrex_utils
from markets import market_operations


class Portfolio(object):
    """
    """
    def __init__(self, dataframe=None):
        """
        Read portfolio from API
        """
        if dataframe is not None:
            self.dataframe = dataframe
        else:
            self.dataframe = bittrex_utils.dataframe()

        if self.dataframe.empty:
            self.dataframe = pd.DataFrame([], columns=['Balance', 'Available', 'Pending', 'CryptoAddress',
                                                          'Requested', 'Uuid'])
            self.dataframe.index.name = 'Currency'

    def total_value(self, market, intermediate_currencies):
        """
        Compute the total amount of the portfolio in 'base' currency ('ETH' and 'BTC' for the time being but not USDT)
        """
        return self.value_per_currency(market, intermediate_currencies).sum()

    def value_per_currency(self, market, intermediate_currencies):
        portfolio = self.dataframe

        return portfolio.apply(lambda x: market_operations.currency_value(market, [x.name] + intermediate_currencies) * x['Balance'],
                               axis=1)
    def mock_buy(self, buy):
        """
        This is a method that mocks sending a buy/sell order to the client and its execution.
        After this method executes, we'll assume that we buy/sell whatever we requested at the requested prices
        
        I don't understand if bittrex client talks in usdt, base or currency when placing orders. I'm just
        mocking the result here, not the call
        
        :param buy: 
        :return: 
        """

        # There is 0.25% cost on each buy/sell transaction. Although exchanging ETH for BTC shows as two transactions
        # in 'buy' and should pay 0.25% only once, most transactions in 'buy' should pay the 0.25%. I'm going to
        # overestimate the transaction cost by paying the 0.25% for every transaction in buy
        # when we want to buy X, we end up with x * (1 - cost)
        # when we want to sell X, we end up with x * (1 - cost) base. I'm modeling this as we actuall sold
        # x * (1 + cost)
        buy = buy.map(apply_transaction_cost)
        self.dataframe['Balance'] += buy
        self.dataframe['Available'] += buy

    def ideal_rebalance(self, market, state, intermediate_currencies):
        """
        Given a state, return the amount to buy (+) or sell (-) for each quantity to achieve this balance.
        
        At this point we don't look at trading costs, sinking currencies, etc
        """
        total_value = self.total_value(market, ['BTC', 'USDT'])

        df = pd.merge(self.dataframe, state, left_index=True, right_index=True, how='outer')      # if state has new cryptocurrencies there will be NaNs
        df.fillna(0, inplace=True)

        df.loc[:, 'target_usdt'] = df['Weight'] * total_value
        df.loc[:, 'target_currency'] = df.apply(
            lambda x: x.target_usdt / market_operations.currency_value(market, [x.name] + intermediate_currencies),
            axis = 1)

        df.loc[:, 'Buy'] = df['target_currency'] - df['Available']
        return df['Buy']


    def rebalance(self, market, state, intermediate_currencies):
        """
        Given a state, buy/sell positions to approximate target_portfolio
        
        base_currency:  base currency to do computations
        threshold:  currencies are only balanced if difference with target is above/below this threshold (express
                    as a percentage)
        """
        buy = self.ideal_rebalance(market, state, intermediate_currencies)
        buy = buy.apply(apply_transaction_cost)
        self.dataframe = pd.merge(self.dataframe, buy.to_frame(), left_index=True, right_index=True, how='outer')
        self.dataframe.fillna(0, inplace=True)

        self.dataframe['Available'] += self.dataframe['Buy']
        self.dataframe['Balance'] += self.dataframe['Buy']
        self.dataframe.drop('Buy', axis=1, inplace=True)


def apply_transaction_cost(buy):
    """ buy is a float, the amount of either currency or dollars to buy (if positive) or sell (if negative)
    """
    try:
        buy *= 1.0
    except:
        raise IOError('buy should be numeric')

    if buy > 0:
        buy -= buy * 0.25/100
    else:
        buy += buy * 0.25/100

    return buy

def start_portfolio(market, state, base, value):
    """
    We first start a portfolio that has just 'value' in 'base' and then execute ideal_rebalance on it
    :param market: 
    :param state: 
    :param base: 
    :param value: 
    :return: 
    """
    dataframe = pd.DataFrame({'Balance': value, 'Available': value, 'Pending': 0}, index=[base])
    portfolio = Portfolio(dataframe=dataframe)

    return portfolio


def uniform_state(market, N, include_usd=True):
    """
    
    :param market: DataFrame with market conditions. The 'N' currencies with the most volume will be used to define a
        state
    :param N: number of cryptocurrencies to include
    :param currencies: dict linking currencies to the values of the 'state'
    :param include_usd: If true, usd will be added to the list of cryptocurrencies to hold (even though it is not).
    :return: Dataframe with the weight of each currency (1/N)
    """
    volumes_df = market_operations.usd_volumes(market)
    volumes_df.drop('USDT', axis=0, inplace=True)

    currencies = volumes_df.head(N).index.tolist()
    assert 'USDT' not in volumes_df.index
    if include_usd:
        currencies[-1] = 'USDT'

    state = pd.DataFrame([1. / N] * N, index=currencies, columns=['Weight'])

    return state
