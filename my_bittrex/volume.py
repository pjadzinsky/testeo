import os
import time

import numpy as np
import pandas as pd

from bittrex import bittrex

import credentials

client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)


class Portfolio(object):
    def __init__(self, target_portfolio_file=None, portfolio_file=None):
        self.portfolio_file = portfolio_file
        self.target_portfolio_file = target_portfolio_file
        self.market = Market()

        self.portfolio = self.get_portfolio(self.portfolio_file)
        if target_portfolio_file is None:
            self.target_portfolio = self.portfolio
        else:
            self.target_portfolio = self.get_portfolio(self.target_portfolio_file)


    def get_portfolio(self, portfolio_file=None):
        """
        Read portfolio from file (create one if portfolio_file given but file is missing) or API if portfolio_file
        is not given
        
        :return: Dataframe indexed by 'Currency' with our portfolio
        """
        if portfolio_file:
            try:
                df = pd.read_csv(portfolio_file, index_col=0)
            except IOError:
                df = start_new_portfolio(10, 'BTC', 1, portfolio_file=portfolio_file)
            except Exception as e:
                raise e
        else:
            df = _to_df(client.get_balances()['result'], 'Currency')

        return df

    def value(self, base):
        """
        Compute the total amount of the portfolio in 'base' currency ('ETH' and 'BTC' for the time being but not USDT)
        """

        total = 0
        for currency, series in self.portfolio.iterrows():
            total += series['Balance'] * self.market.currency_cost_in_base_currency(currency, base)

        return total


        return get_total_balance(self.balances, base=base)

    def rebalance(self, base_currency):
        """
        Given a state, buy/sell positions to approximate target_portfolio
        """
        portfolio = self.portfolio.copy()
        summaries = self.market.summaries()

        total_value = self.value(base_currency)
        mean = total_value / len(portfolio)

        balances = portfolio['Balance'].tolist()
        currencies = portfolio.index.tolist()
        currency_in_base = [self.market.currency_cost_in_base_currency(c, base_currency) for c in currencies]

        portfolio.loc[:, 'Value'] = [b * cb for b, cb in zip(balances, currency_in_base)]
        print portfolio

        """
        balances.loc[:, 'market_value'] = balances['Available'] * balances['Last']
        mean = balances['market_value'].mean()

        balances.loc[:, 'excess'] = balances['market_value'] - mean

        balances.loc[:, 'delta'] = balances.apply(
            lambda x: x['excess'] / self.market.currency_cost_in_base_currency(x.name, base_currency), axis=1)
        print balances.head()
        """


class Market(object):
    def __init__(self, cache_timeout_sec=600):
        self._timestamp = 0
        self._cache_timeout_sec = cache_timeout_sec

    def summaries(self):
        """
        Accessor with caching for get_summaries()
        :return: 
        """
        if self._timestamp + self._cache_timeout_sec > time.time():
            pass
        else:
            print int(time.time())
            self._summaries = get_summaries()
            self._timestamp = time.time()

        return self._summaries

    def currency_cost_in_base_currency(self, currency, base_currency):
        """
        :param currency:
        :param base_currency: 
        :return: 
        """

        summaries = self.summaries()
        potential_market_name = base_currency + "-" + currency
        reversed_market_name = currency + "_" + base_currency
        if currency == base_currency:
            return 1.0
        elif potential_market_name in summaries.index:
            return summaries.loc[potential_market_name, 'Last']
        elif reversed_market_name in summaries.index:
            return 1.0 / summaries.loc[reversed_market_name, 'Last']
        else:
            msg = "currency: {0} and base_currency {1} don't make a valid market name in 'summaries'".format(
                currency, base_currency)
            raise ValueError(msg)

    def usd_volumes(self):
        """
        
        :return: pandas DataFrame indexed by currencies with one column ('USDT Volume')
                 DataFrame is sorted in descending order (row 0 has the currency with the highest volume)
        """
        currencies_df = get_currencies()

        volumes_df = pd.DataFrame()

        for currency in currencies_df.index:
            volumes_df.loc[currency, 'USDT Volume'] = self.currency_volume(currency)

        volumes_df.sort_values('USDT Volume', inplace=True, ascending=False)
        return volumes_df

    def currency_volume(self, currency):
        """
        Return total volume for currency in base_currency
        
        :param currency: str, any currency in bittrex
        :param base_currency: either 'USDT', 'BTC', 'ETH'
        :return: 
        """
        summaries_df = self.summaries()

        BTC_marketname = "BTC" + "-" + currency
        ETH_marketname = "ETH" + "-" + currency
        USD_marketname = "USDT" + "-" + currency
        usd_volume = 0

        USDT_BTC = self.currency_cost_in_base_currency('BTC', 'USDT')
        USDT_ETH = self.currency_cost_in_base_currency('ETH', 'USDT')

        if BTC_marketname in summaries_df.index:
            usd_volume += summaries_df.loc[BTC_marketname, 'BaseVolume'] * USDT_BTC

        if ETH_marketname in summaries_df.index:
            usd_volume += summaries_df.loc[ETH_marketname, 'BaseVolume'] * USDT_ETH

        if USD_marketname in summaries_df.index:
            usd_volume += summaries_df.loc[USD_marketname, 'BaseVolume']

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


def get_summaries():
    """
    :return: Dataframe indexed by "MarketName" with market data about each currency
    """
    response = client.get_market_summaries()
    if response['success']:
        df = _to_df(response['result'], 'MarketName')

    # it becomes simpler later on if we treat USDT as another crypto-currency
    # treated in BTC and ETH as anything else
    #df = df.append(_invert_base(df.loc['USDT-ETH']))
    #df = df.append(_invert_base(df.loc['USDT-BTC']))


    market_name = df.index.values
    base_currency = [mn.split('-') for mn in market_name]
    df.loc[:, 'Base'] = [bc[0] for bc in base_currency]
    df.loc[:, 'Currency'] = [bc[1] for bc in base_currency]

    return df


def start_new_portfolio(N, base_currency, value, portfolio_file=None):
    """
    Start a new blanace out of the N crypto currencies with more volume
    balanced is generated as a DF and stored as a csv under portfolio_file if given
    
    :param N: number of cryptocurrencies to use.
    :param base_currency: str, currency we are funding the portfolio with ('ETH' or 'BTC')
    :param value: float, initial value of portfolio in 'base_currency'
    :return: 
    """
    assert(base_currency in ['ETH', 'BTC'])
    market = Market()
    volumes_df = market.usd_volumes()
    selected_currencies = volumes_df.head(N).index.tolist()

    balances = [value / market.currency_cost_in_base_currency(c, base_currency) / N for c in selected_currencies]

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
    if portfolio_file:
        df.to_csv(portfolio_file)

    return df


'''
def _invert_base(summary_row):
    """
    Invert the relationshipt between Base and Currency for a given
    row of summary
    
    :param summary_row: 
    :return: series with same index as summary_row
    """
    output = summary_row.copy()
    output['Ask'] = 1.0 / summary_row['Ask']
    output['BaseVolume'] = summary_row['BaseVolume'] / summary_row['Last']
    output['Bid'] = 1.0 / summary_row['Bid']
    output['Created'] = summary_row['Created']
    output['High'] = 1.0 / summary_row['Low']
    output['Last'] = 1.0 / summary_row['Last']
    output['Low'] = 1.0 / summary_row['High']
    output['OpenBuyOrders'] = summary_row['OpenSellOrders']
    output['OpenSellOrders'] = summary_row['OpenBuyOrders']
    output['PrevDay'] = 1.0 / summary_row['PrevDay']
    output['TimeStamp'] = summary_row['TimeStamp']
    output['Volume'] = summary_row['Volume']
    if 'Currency' in summary_row:
        output['Base'] = summary_row['Currency']
    if 'Base' in summary_row:
        output['Currency'] = summary_row['Base']

    # new MarketName
    new_currency, new_base = summary_row.name.split('-')
    output.rename(new_base + '-' + new_currency, inplace=True)
    return output
    
def get_USD_volume():
    summaries = get_summaries()
    summaries.loc[:, 'USD volume'] = summaries['BaseVolume']

    for base in set(summaries['Base']):
        try:
            if base == "USDT":
                base_last = 1
            else:
                base_last = summaries.loc['USDT-' + base, 'Last']
            summaries.loc[summaries['Base']==base, 'USD volume'] *= base_last
        except:
            summaries.loc[summaries['Base']==base, 'USD volume'] = None

    return summaries[['Currency', 'USD volume']].groupby('Currency').sum().sort_values('USD volume')


'''

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


