import time

import pandas as pd

from bittrex import bittrex
import credentials
import memoize

client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)


currencies_timestamp = float('-inf')
currencies_df = None

@memoize.memoized
def currencies_df():
    """
    
    :return: Dataframe indexed by "Currency" with available currencies. Columns are:
     [u'BaseAddress', u'CoinType', u'CurrencyLong', u'IsActive', u'MinConfirmation', u'Notice', u'TxFee']
    """
    return _to_df(client.get_currencies()['result'], 'Currency')


def get_balances():
    """
    bittrex.client returns balances as a list of dictionaries with these keys:
    Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid
    
    :return:  pd.Dataframe that can be used with portfolio.Portfolio(df)
              It is indexed by "Currency" and has columns Available, Balance, CryptoAddress, Pending, Requested, Uuid
    """
    return _to_df(client.get_balances()['result'], 'Currency')


def get_current_market():
    """
    bittrex.client returns market_summaries as a list of dictionaries with these keys:
    'Ask', 'BaseVolume', 'Bid', 'Created', 'High', 'Last', 'Low', 'MarketName', 'OpenBuyOrders', 'OpenSellOrders',
     'PrevDay', 'TimeStamp', 'Volume'

    :return:    pd.Dataframe that can be used with market.Market(df)
                It is indexed by "MarketName" and has all other keys as columns
    
    :return: 
    """
    prices_df = _to_df(client.get_market_summaries()['result'], 'MarketName')
    timestamp = int(time.time())
    return timestamp, prices_df


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




