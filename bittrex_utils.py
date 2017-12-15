import os
import time

from base64 import b64decode
from bittrex import bittrex
import boto3
import gflags
import pandas as pd

import config
import memoize
print 'Finished with imports in', __file__

FLAGS = gflags.FLAGS


# Expand bittrex.Bittrex to include logger
class Bittrex(bittrex.Bittrex):
    def api_query(self, method, options=None):
        # Override api_query to log error messages
        response = super(Bittrex, self).api_query(method, options=options)

        return response


public_client = Bittrex('', '')
if 'BITTREX_KEY_ENCRYPTED' in os.environ:
    # Decrypt code should run once and variables stored outside of the function
    # handler so that these are decrypted once per container
    ENCRYPTED_KEY = os.environ['BITTREX_KEY_ENCRYPTED']
    ENCRYPTED_SECRET = os.environ['BITTREX_SECRET_ENCRYPTED']

    import pudb; pudb.set_trace()

    BITTREX_KEY = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_KEY))['Plaintext']
    BITTREX_SECRET = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_SECRET))['Plaintext']
    private_client = Bittrex(BITTREX_KEY, BITTREX_SECRET)

currencies_timestamp = float('-inf')
currencies_df = None



@memoize.memoized
def currencies_df():
    """
    
    :return: Dataframe indexed by "Currency" with available currencies. Columns are:
     [u'BaseAddress', u'CoinType', u'CurrencyLong', u'IsActive', u'MinConfirmation', u'Notice', u'TxFee']
    """
    response = public_client.get_currencies()
    result = _to_df(response['result'], 'Currency')
    return result


@memoize.memoized
def market_names():
    return [r['MarketName'] for r in public_client.get_markets()['result']]


def get_balances():
    """
    bittrex.client returns balances as a list of dictionaries with these keys:
    Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid
    
    :return:  pd.Dataframe that can be used with portfolio.Portfolio(df)
              It is indexed by "Currency" and has columns Available, Balance, CryptoAddress, Pending, Requested, Uuid
    """
    response = private_client.get_balances()
    result = _to_df(response['result'], 'Currency')
    result = result[result['Balance'] > 0]
    return result


def get_balance(currency):
    """
    bittrex.client returns balances as a list of dictionaries with these keys:
    Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid
    
    :return:  pd.Dataframe that can be used with portfolio.Portfolio(df)
              It is indexed by "Currency" and has columns Available, Balance, CryptoAddress, Pending, Requested, Uuid
    """
    response = private_client.get_balance(currency)
    result = response['result']
    return result


def get_current_market():
    """
    bittrex.client returns market_summaries as a list of dictionaries with these keys:
    'Ask', 'BaseVolume', 'Bid', 'Created', 'High', 'Last', 'Low', 'MarketName', 'OpenBuyOrders', 'OpenSellOrders',
     'PrevDay', 'TimeStamp', 'Volume'

    :return:    pd.Dataframe that can be used with market.Market(df)
                It is indexed by "MarketName" and has all other keys as columns
    
    :return: 
    """
    response = public_client.get_market_summaries()
    prices_df = _to_df(response['result'], 'MarketName')
    timestamp = int(time.time())
    return timestamp, prices_df


def cancel_all_orders():
    response = private_client.get_open_orders('')
    for order in response['result']:
        private_client.cancel(order['OrderUuid'])


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

print 'finished loading', __file__
