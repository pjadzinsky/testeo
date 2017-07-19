import time
import json
import numpy as np
import pandas as pd

from bittrex import bittrex
import credentials

client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)


class Portfolio(object):
    """
    A portfolio is the type and amount of each cryptocurrency held.
    There is a desired 'state' and due to fluctuations some currencies will have more (or less) value than their
    desired target 'state'. We'll rebalance them periodically.
    To avoid spending too much in commissions when rebalancing we have a 'threshold' and we only 'rebalance
    cryptocurrencies that increased (or decreased) more than 'threshold' (as a percentage) from desired 'state'.
    For example is the desired state is 100 and the threshold is 0.1 we'll sell only if the current value is at or above
    110 (and buy if the current value is at or below 90)
    To prevent from buying too much of a sinking currency we are going to put bounds on either the price and/or the
    quantities (not clear yet). One idea is to compute the ratio between the current balance and the initial balance
    per currency and then say that no currency can have a ratio that is N times bigger than the average ratio.
    """
    def __init__(self, portfolio=None):
        """
        Read portfolio from API
        """
        if portfolio is not None:
            self.portfolio = portfolio
        else:
            self.portfolio = _to_df(client.get_balances()['result'], 'Currency')

    def value(self, market, intermediate_currencies):
        """
        Compute the total amount of the portfolio in 'base' currency ('ETH' and 'BTC' for the time being but not USDT)
        """
        portfolio = self.portfolio

        total = 0
        for currency, series in portfolio.iterrows():
            total += series['Balance'] * market.currency_value([currency] + intermediate_currencies)

        return total

    def rebalance(self, market, state, initial_portfolio, base_currency, threshold):
        """
        Given a state, buy/sell positions to approximate target_portfolio
        
        base_currency:  base currency to do computations
        threshold:  currencies are only balanced if difference with target is above/below this threshold (express
                    as a percentage)
        """
        # value of all portfolio in base_currency
        total_value = self.value(market, [base_currency])

        # amount in each currency if balanced according to state
        target_value_in_base = total_value * state

        # compute money per currency (in base_currency)
        balances = self.portfolio['Balance'].tolist()
        currencies = self.portfolio.index.tolist()
        currency_in_base = [market.currency_value([c, base_currency]) for c in currencies]
        market_value = [b * cb for b, cb in zip(balances, currency_in_base)]

        # compute amount to sell (buy if negative) to maintain initial 'state'
        excess_in_base = market_value - target_value_in_base
        excess_percentage = [e / t for e, t in zip(excess_in_base, target_value_in_base)]
        sell_in_base = [e if np.abs(ep) > threshold else 0 for e, ep in zip(excess_in_base, excess_percentage)]

        sell_in_currency = [sb / cb for sb, cb in zip(sell_in_base, currency_in_base)]

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


class Market(object):
    def __init__(self, cache_timeout_sec=600, json_blob=None):
        self._timestamp = 0
        self._cache_timeout_sec = cache_timeout_sec
        self._json_blob = json_blob
        self.summaries(json_blob=json_blob)

    def summaries(self, json_blob=None):
        """
        Accessor with caching to call client.get_market_summaries()
        :return: Dataframe indexed by "MarketName" with market data about each currency
        """
        if self._timestamp + self._cache_timeout_sec > time.time():
            return self._summaries

        elif json_blob:
            response = json.loads(json_blob)
            import pprint
            pprint.pprint( response)
        else:
            print "about to call client.get_market_summaries()"
            print int(time.time())
            response = client.get_market_summaries()

        self._timestamp = time.time()
        if response['success']:
            df = _to_df(response['result'], 'MarketName')

            market_name = df.index.values
            base_currency = [mn.split('-') for mn in market_name]
            df.loc[:, 'Base'] = [bc[0] for bc in base_currency]
            df.loc[:, 'Currency'] = [bc[1] for bc in base_currency]
            self._summaries = df
        else:
            raise IOError

        return self._summaries

    def currency_value(self, currencies):
        """
        Convert currencies[0] into currencies[1] then into currencies[2], ..., until currencies[-1]
        """

        if len(currencies) == 0:
            return 0
        elif len(currencies) == 1:
            return 1

        currency = currencies[0]
        base = currencies[1]

        potential_market_name = base + "-" + currency
        reversed_market_name = currency + "-" + base
        if currency == base:
            cost = 1.0
        elif potential_market_name in self.summaries().index:
            cost = self.summaries().loc[potential_market_name, 'Last']
        elif reversed_market_name in self.summaries().index:
            cost = 1.0 / self.summaries().loc[reversed_market_name, 'Last']
        else:
            cost = 0

        return cost * self.currency_value(currencies[1:])

    def usd_volumes(self, base, intermediate_currencies):
        """
        
        :return: pandas DataFrame indexed by currencies with one column ('USDT Volume')
                 DataFrame is sorted in descending order (row 0 has the currency with the highest volume)
        """
        currencies_df = get_currencies()

        volumes_df = pd.DataFrame()

        for currency in currencies_df.index:
            volumes_df.loc[currency, 'USDT Volume'] = self.currency_volume(currency, base, intermediate_currencies)

        volumes_df.sort_values('USDT Volume', inplace=True, ascending=False)
        return volumes_df

    def currency_volume(self, currency, base, intermediate_currencies):
        """
        Return total volume for currency in base_currency
        
        :param currency: str, any currency in bittrex
        :param base_currency: either 'USDT', 'BTC', 'ETH'
        :return: 
        """
        summaries_df = self.summaries()

        usd_volume = 0

        for intermediate_currency in intermediate_currencies:
            market_name = intermediate_currency + "-" + currency
            cost = self.currency_value([intermediate_currency, base])

            if market_name in summaries_df.index:
                usd_volume += summaries_df.loc[market_name, 'BaseVolume'] * cost

        return usd_volume


def _to_df(response, new_index=None):
    """
    
    :param summaries: 
    :return: pd.DataFrame: Columns are the keys into each 'summaries'
    
    """
    df = pd.DataFrame([])
    for r in response:
        df = df.append(r, ignore_index=True)

    if new_index and not df.empty:
        df.set_index(new_index, drop=True, inplace=True)
    return df


def get_currencies():
    """
    
    :return: Dataframe indexed by "Currency" with available currencies
    """
    response = client.get_currencies()
    if response['success']:
        currencies_df = _to_df(response['result'], 'Currency')

    return currencies_df


def start_new_portfolio(market, state, base_currency, value):
    """
    Start a new blanace out of the N crypto currencies with more volume
    balanced is generated as a DF and stored as a csv under portfolio_file if given
    
    :param state: iterable with relative representation of each cryptocurrencies.
                  len(state) is the number of cryptocurrencies to buy.
                  state[i] / sum(state) is the fraction of 'value' that would be invested in currency[i]
    :param base_currency: str, currency we are funding the portfolio with ('ETH' or 'BTC')
    :param value: float, initial value of portfolio in 'base_currency'
    :return: 
    """
    assert(base_currency in ['ETH', 'BTC'])
    volumes_df = market.usd_volumes('base_currency', ['BTC', 'USDT'])
    N = len(state)
    selected_currencies = volumes_df.head(N).index.tolist()

    initial_balance_in_base = np.array(state) * value * 1.0 / sum(state)
    assert(sum(initial_balance_in_base) == value)

    balances = [initial / market.currency_value([c, 'BTC', 'USDT']) for initial, c in
                zip(initial_balance_in_base, selected_currencies)]

    df = pd.DataFrame({
        "Currency": selected_currencies,
        "Balance" : balances,
        "Available" : balances,
        "Pending" : [0] * N,
        "CryptoAddress" : ["DLxcEt3AatMyr2NTatzjsfHNoB9NT62HiF"] * N,
        "Requested" : [False] * N,
        "Uuid" : [None] * N
        })

    df.set_index('Currency', drop=True, inplace=True)

    return Portfolio(portfolio=df)


def _market_names(currency, base_currency):
    """
    :param currency: str, 
    :param base_currency: str, base currency
    :return: market name if currency is traded in base_currency, None otherwise
    """
    currencies = get_currencies().index
    if currency == base_currency:
        answer = None
    if currency not in currencies:
        answer = None
    elif base_currency == 'USDT' and currency not in ['ETH', 'BTC']:
        answer = None
    else:
        answer = base_currency + "-" + currency

    return answer

