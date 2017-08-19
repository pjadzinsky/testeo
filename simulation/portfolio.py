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
        import pudb
        pudb.set_trace()
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

    def ideal_rebalance(self, market, state):
        """
        Given a state, return the amount to buy (+) or sell (-) for each quantity to achieve this balance.
        
        At this point we don't look at trading costs, sinking currencies, etc
        """
        temp_portfolio = pd.merge(self.dataframe, state, how='outer', left_index=True, right_index=True)
        temp_portfolio.fillna({'Balance': 0, 'Available': 0, 'Pending': 0, 'CryptoAddress': '', 'Requested': True,
                               'Uuid': '', 'Weight': 0}, inplace=True)
        # We just added all currencies in 'state' to 'temp_portfolio', but we also need them in
        self.dataframe = temp_portfolio.drop(['Weight'], axis=1)

        # total_value of each investment in 'USDT'
        temp_portfolio['Value (USDT)'] = temp_portfolio.apply(
            lambda x: market_operations.currency_value(market, [x.name, 'BTC', 'USDT']) * x['Balance'], axis=1)

        total_value = temp_portfolio['Value (USDT)'].sum()

        temp_portfolio['Target_USDT'] = total_value * temp_portfolio['Weight']/ temp_portfolio['Weight'].sum()
        temp_portfolio['Buy_USDT'] = temp_portfolio['Target_USDT'] - temp_portfolio['Value (USDT)']
        temp_portfolio['Buy'] = temp_portfolio.apply(
            lambda x: x['Buy_USDT'] / market_operations.currency_value(market, [x.name, 'BTC', 'USDT']), axis=1)

        return temp_portfolio['Buy']


    def rebalance(self, market, state, initial_portfolio, base_currency, threshold):
        """
        Given a state, buy/sell positions to approximate target_portfolio
        
        base_currency:  base currency to do computations
        threshold:  currencies are only balanced if difference with target is above/below this threshold (express
                    as a percentage)
        """
        # total_value of all portfolio in base_currency
        total_value = self.total_value(market, [base_currency])

        # amount in each currency if balanced according to state
        target_value_in_base = total_value / np.sum(state)

        currencies = self.dataframe.index.tolist()

        _rebalance(currency, target_value)
        # compute money per currency (in base_currency)
        balances = self.dataframe['Balance'].tolist()
        currencies = self.dataframe.index.tolist()
        currency_in_base = [market_operations.currency_value(market, [c, base_currency]) for c in currencies]
        market_value = [b * cb for b, cb in zip(balances, currency_in_base)]

        # compute amount to sell (buy if negative) to maintain initial 'state'
        excess_in_base = market_value - target_value_in_base
        excess_percentage = [e / t for e, t in zip(excess_in_base, target_value_in_base)]
        sell_in_base = [e if np.abs(ep) > threshold else 0 for e, ep in zip(excess_in_base, excess_percentage)]

        sell_in_currency = [cb / sb for sb, cb in zip(sell_in_base, currency_in_base)]

        # compute the new Balance for each currency after buying/selling for rebalancing
        new_balances = np.array([b + sc for b, sc in zip(balances, sell_in_currency)])

        # what would the new average ratio between current and original balances be if we were to
        # sell 'sell_in_currency'?
        mean_ratio = np.mean(initial_portfolio.portfolio['Balance'] / new_balances)
        # I want to limit buying/selling such that the ratio for each currency is not more than N times the mean.
        # This means that new_balances has to be the min between new_balances computed above and N * new_balances / mean_ratio
        N = len(state)
        new_balances = [min(nb, N * nb / mean_ratio) for nb in new_balances]

        sell_in_currency = [nb - b for nb, b in zip(new_balances, balances)]

        return sell_in_currency


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

    # compute what needs to be bought (+) or sold (-) to balance the portfolio
    buy = portfolio.ideal_rebalance(market, state)

    # now balance the portfolio
    portfolio.mock_buy(buy)

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
    if not include_usd:
        volumes_df.drop('USDT', axis=0, inplace=True)

    currencies = volumes_df.head(N).index.tolist()
    if include_usd:
        currencies[-1] = 'USDT'

    state = pd.DataFrame([1. / N] * N, index=currencies, columns=['Weight'])

    return state
