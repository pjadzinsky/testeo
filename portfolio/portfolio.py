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
import gflags

import bittrex_utils
import log

import config

gflags.DEFINE_boolean('simulating', True, "if set, 'mock_buy' is used instead of the real 'buy'")
FLAGS = gflags.FLAGS
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
    def from_state(cls, market, state, base, value):
        p = cls._start_portfolio(market, state, base, value)
        return p

    @classmethod
    def from_simulation_index(cls, sim_index):
        params_df = pd.read_csv(config.PARAMS, index_col=0)
        sim_params = params_df.loc[sim_index]
        p = cls.from_simulation_params(sim_params)
        return p

    @classmethod
    def from_simulation_params(cls, market, sim_params):
        base = sim_params['base']
        value = sim_params['value']

        state = sim_params.to_frame()
        for key in config.PARAMS_INDEX_THAT_ARE_NOT_CURRENCIES:
            if key in state.index:
                state.drop(key, inplace=True, axis=0)
        state.columns = ['Weight']
        p = cls._start_portfolio(market, state, base, value)
        return p

    @classmethod
    def from_bittrex(cls):
        return cls(bittrex_utils.get_balances())


    def copy(self):
        cls = self.__class__
        new_df = self.dataframe.copy()
        return cls(new_df)


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
    def ideal_rebalance(self, market, state, intermediate_currencies):
        """
        Given market, state and intermediate_currencies return the amount to buy (+) or sell (-) for each currency
        to achieve perfect balance.
        
        At this point we don't look at trading costs, sinking currencies, etc
        
        returned dataframe has columns:
        target_base:    the value in 'base' we should have in each currency after rebalancing
        target_currency:    the ideal amount of each currency that achieves this ideal rebalancing
        Buy:            the amount of currency that we have to buy (if > 0) or sell (if < 0) to obtain
                        target_currency
        Buy (base):     Amount of base needed for the transaction (not taking transactions costs into account)
        intermediate_currencies:    each currency in 'state' will be converted to values in 'base' where base is
                                    intermediate_currencies[0] and the conversion is done by traversing
                                    from currency in state to intermediate_currencies[-1], then to
                                    intermediate_currencies[-2], ..., ending in intermediate_currencies[0]
                                    
                                    most likely this is going to be either:
                                        ['USDT', 'BTC']
                                        ['USDT', 'ETH']
                                        ['BTC']
                                        ['ETH']
        """
        total_value = self.total_value(market, intermediate_currencies)

        buy_df = pd.merge(self.dataframe, state, left_index=True, right_index=True, how='outer')      # if state has new cryptocurrencies there will be NaNs
        buy_df.fillna(0, inplace=True)

        base = intermediate_currencies[0]

        buy_df.loc[:, 'target_base'] = buy_df['Weight'] * total_value
        buy_df.loc[:, 'currency_in_base'] = buy_df.apply(
            lambda x: market.currency_chain_value([base] + intermediate_currencies + [x.name]), axis=1)
        buy_df.loc[:, 'target_currency'] = buy_df['target_base'] / buy_df['currency_in_base']

        buy_df.loc[:, 'Buy'] = buy_df['target_currency'] - buy_df['Balance']
        buy_df.loc[:, 'Buy ({base})'.format(base=intermediate_currencies[0])] = buy_df.apply(
            lambda x: x.Buy * market.currency_chain_value([base] + intermediate_currencies + [x.name]),
            axis=1
        )

        return buy_df

    def rebalance(self, market, state, intermediate_currencies, min_percentage_change, by_currency=False):
        """
        Given a state, buy/sell positions to approximate target_portfolio
        
        base_currency:  base currency to do computations
        threshold:  currencies are only balanced if difference with target is above/below this threshold (express
                    as a percentage)
        """
        buy_df = self.ideal_rebalance(market, state, intermediate_currencies)
        # apply transaction costs
        buy_df.loc[:, 'Buy'] = buy_df['Buy'].apply(apply_transaction_cost)

        base = intermediate_currencies[0]

        # we only buy/sell if movement is above 'min_percentage_change'. However, this movement could be in the
        # amount of cryptocurrency we own (by_currency=True) or in the amount of 'base' it represents (by_currency=False)
        for currency in buy_df.index:
            if by_currency:
                # if 'buy_df['Buy'] represents less than 'min_percentage_change' from 'position' don't do anything
                percentage_change = np.abs(buy_df.loc[currency, 'Buy']) / buy_df.loc[currency, 'Balance']
            else:
                # if 'buy_df['Buy (base)'] represents less than 'min_percentage_change' from 'position' don't do anything
                percentage_change = np.abs(buy_df.loc[currency, 'Buy ({})'.format(base)]) / \
                                    buy_df.loc[currency, 'target_base']
            buy_df.loc[currency, "change"] = percentage_change
            if percentage_change < min_percentage_change:
                buy_df.loc[currency, 'Buy'] = 0

        # if 'base' is in self.dataframe, remove it. Each transaction is simulated against 'base' but we don't
        # buy/sell 'base' directly. Not doing this will lead to problems and double counting
        if base in buy_df.index:
            buy_df.loc[base, 'Buy'] = 0
            buy_df.loc[base, 'Buy ({})'.format(base)] = 0

        if FLAGS.simulating:
            self.mock_buy(buy_df[['Buy', 'Buy ({})'.format(base), 'change']])
        else:
            self.buy(buy_df, base)

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

        # get 'base' name from the column named 'Buy (base)'
        column = [c for c in buy_df.columns if c.startswith("Buy (")][0]
        base = column[5:-1]

        # the 'index' in buy_df might not be the same as in self.dataframe. That's why we start merging based on
        # index and we use 'outer'.
        self.dataframe = pd.merge(self.dataframe, buy_df, left_index=True, right_index=True, how='outer')
        #  If new values are added to index there will be NaN
        self.dataframe.fillna(0, inplace=True)
        self.dataframe['Balance'] += self.dataframe['Buy']
        self.dataframe['Available'] += self.dataframe['Buy']

        self.dataframe.loc[base, 'Balance'] -= self.dataframe[column].sum()
        self.dataframe.loc[base, 'Available'] -= self.dataframe[column].sum()
        self.dataframe.drop(['Buy', column, 'change'], inplace=True, axis=1)

    def buy(self, buy_df, base_currency):
        """
        Send buy/sell requests for all rows in buy_df
        
        :param buy_df: 
        :param base_currency: 
        :return: 
        """
        currencies = buy_df.index.tolist()
        market_names = [_market_name(base_currency, currency) for currency in currencies]
        amount_to_buy = buy_df['Buy ({})'.format(base_currency)]

        for currency, market_name, amount in zip(currencies, market_names, amount_to_buy):
            if not market_name:
                continue

            if amount > 0:
                msg = 'Would send BUY order'
                trade = bittrex_utils.client.buy_market
            else:
                msg = 'Would send SELL order'
                trade = bittrex_utils.client.sell_market
                amount *= -1
            print msg
            print 'Market_name: {}, amount: {}'.format(market_name, amount)

            import pudb
            pudb.set_trace()
            response = trade(market_name, amount)
            log.info(response)




def _market_name(base, currency):
    name = base + '-' + currency
    if name in bittrex_utils.market_names():
        return name

    return None


def state_from_largest_markes(market, N, include_usd):
    state = _uniform_state(market, N, include_usd=include_usd)
    return state


def state_from_currencies(currencies):
    weights = 1.0 / len(currencies)
    state = pd.DataFrame({'Weight': weights}, index=currencies)
    return state


def random_state(currencies, N):
    """ Generate a random makret using 'N' currencies from 'currencies'
    """
    currencies_to_use = np.random.choice(currencies, size=N, replace=False)
    return state_from_currencies(currencies_to_use)


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


def currencies_from_state(state):
    currencies = state[state['Weight'] > 0].index.values
    return currencies


def n_from_state(state):
    return len(currencies_from_state(state))


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

