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
    
    :return: Dataframe indexed by "Currency" with available currencies columns are:
     [u'BaseAddress', u'CoinType', u'Currency', u'CurrencyLong', u'IsActive', u'MinConfirmation', u'Notice', u'TxFee']
    """
    response = client.get_currencies()
    results = response['result']
    df = pd.DataFrame([])
    for r in results:
        df = df.append(pd.Series(r), ignore_index=True)

    return df



