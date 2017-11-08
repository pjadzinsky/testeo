import os
import time

from base64 import b64decode
from bittrex import bittrex
import boto3
import gflags
import pandas as pd

import log
import memoize

FLAGS = gflags.FLAGS

ENCRYPTED_KEY = os.environ['BITTREX_KEY_ENCRYPTED']
BITTREX_KEY = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_KEY))['Plaintext']
ENCRYPTED_SECRET = os.environ['BITTREX_SECRET_ENCRYPTED']
BITTREX_SECRET = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_SECRET))['Plaintext']


# Decrypt code should run once and variables stored outside of the function
# handler so that these are decrypted once per container

currencies_timestamp = float('-inf')
currencies_df = None

# Expand bittrex.Bittrex to include logger
class Bittrex(bittrex.Bittrex):
    def api_query(self, method, options=None):
        # Override api_query to log error messages
        response = super(Bittrex, self).api_query(method, options=options)
        if not response['success']:
            log.error(response['message'])

        return response


client = Bittrex(BITTREX_KEY, BITTREX_SECRET)


@memoize.memoized
def currencies_df():
    """
    
    :return: Dataframe indexed by "Currency" with available currencies. Columns are:
     [u'BaseAddress', u'CoinType', u'CurrencyLong', u'IsActive', u'MinConfirmation', u'Notice', u'TxFee']
    """
    response = client.get_currencies()
    result = _to_df(response['result'], 'Currency')
    return result


@memoize.memoized
def market_names():
    return [r['MarketName'] for r in client.get_markets()['result']]


def get_balances():
    """
    bittrex.client returns balances as a list of dictionaries with these keys:
    Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid
    
    :return:  pd.Dataframe that can be used with portfolio.Portfolio(df)
              It is indexed by "Currency" and has columns Available, Balance, CryptoAddress, Pending, Requested, Uuid
    """
    response = client.get_balances()
    result = _to_df(response['result'], 'Currency')
    return result


def get_balance(currency):
    """
    bittrex.client returns balances as a list of dictionaries with these keys:
    Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid
    
    :return:  pd.Dataframe that can be used with portfolio.Portfolio(df)
              It is indexed by "Currency" and has columns Available, Balance, CryptoAddress, Pending, Requested, Uuid
    """
    response = client.get_balance(currency)
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
    response = client.get_market_summaries()
    prices_df = _to_df(response['result'], 'MarketName')
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

