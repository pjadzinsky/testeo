import time
import os

from base64 import b64decode
import pandas as pd
import memoize

from poloniex import poloniex
from poloniex import utils
import config


class Exchange(object):
    def __init__(self):
        self.public_client = poloniex.PoloniexPublic()
        self.private_client = get_private_client()

    @memoize.memoized
    def currencies_df(self):
        """
        
        :return: Dataframe indexed by "Currency" with columns: 'IsActive', and 'TxFee'
        """
        response = public_client.returnCurrencies()
        result = _to_df(response)

        result.loc[:, 'IsActive'] = ~ result['disabled'].astype(bool)
        result = result[['IsActive', 'txFee']]
        result.columns = ['IsActive', 'TxFee']
        return result


    @memoize.memoized
    def market_names(self):
        response = public_client.returnTicker()
        return response.keys()


    def get_balances(self):
        """
        poloniex.client returns balances as a dictionary linking cryptocurrency to amount, nothing more
        
        :return:  pd.Series
        """
        response = private_client.returnBalances()
        s = pd.Series(response.values(), index=response.keys())
        s = s[s > 0]

        return s


    def get_current_market(self):
        """
        poloniex.client returns a dictionary linking currency pairs to:
            "last":"0.0251",
            "lowestAsk":"0.02589999",
            "highestBid":"0.0251",
            "percentChange":"0.02390438",
            "baseVolume":"6.16485315",
            "quoteVolume":"245.82513926"

        :return:    tuple (timestamp, df)
                    
                    df: pd.Dataframe that can be used with market.Market(df)
                    It is indexed by "MarketName" and has these keys as columns:
                    'Last', 'BaseVolume'
        
        :return: 
        """
        response = public_client.returnTicker()
        prices_df = pd.DataFrame(response.values(), index=response.keys())
        prices_df = prices_df[['last', 'baseVolume']]
        prices_df.columns = ['Last', 'BaseVolume']

        timestamp = int(time.time())
        return timestamp, prices_df


    def cancel_all_orders():
        response = private_client.returnOpenOrders()
        for currency_pair, orders in response.items():
            for order in orders:
                id = order['orderNumber']
                status = private_client.cancelOrder(id)
                if not status['success']:
                    print 'currency_pair', order, id, 'failed to cancel'


def get_private_client():
    private_client = None
    if 'POLONIEX_KEY_ENCRYPTED' in os.environ:
        # Decrypt code should run once and variables stored outside of the function
        # handler so that these are decrypted once per container
        ENCRYPTED_KEY = os.environ['POLONIEX_KEY_ENCRYPTED']
        ENCRYPTED_SECRET = os.environ['POLONIEX_SECRET_ENCRYPTED']

        POLONIEX_KEY = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_KEY))['Plaintext']
        POLONIEX_SECRET = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_SECRET))['Plaintext']
        private_client = poloniex.Poloniex(POLONIEX_KEY, POLONIEX_SECRET)

    if 'POLONIEX_KEY' in os.environ:
        # Decrypt code should run once and variables stored outside of the function
        # handler so that these are decrypted once per container
        POLONIEX_KEY = os.environ['POLONIEX_KEY']
        POLONIEX_SECRET = os.environ['POLONIEX_SECRET']

        private_client = poloniex.Poloniex(POLONIEX_KEY, POLONIEX_SECRET)

    return private_client



def _to_df(response):
    """
    
    :param summaries: 
    :return: pd.DataFrame: Columns are the keys into each 'summaries'
    
    """
    assert isinstance(response, utils.AutoCastDict)

    df = pd.DataFrame([])
    for k, v in response.iteritems():
        row = pd.Series(v.values(), index=v.keys(), name=k)

        df = df.append(row)

    return df

print 'finished loading', __file__
