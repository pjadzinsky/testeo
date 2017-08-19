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


def portfolio_df():
    """
    bittrex.client returns balances as a list of dictionaries with:
    Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid
    
    :return:  Dataframe indexed by "Currency". Columns are:
        Available, Balance, CryptoAddress, Pending, Requested, Uuid
    """
    return _to_df(client.get_balances()['result'], 'Currency')


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




