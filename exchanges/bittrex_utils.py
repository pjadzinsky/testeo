from dateutil import parser
import os
import time

from base64 import b64decode
from bittrex import bittrex
import pandas as pd

import config
import memoize
print 'Finished with imports in', __file__


class Exchange(object):
    def __init__(self):
        self.public_client = bittrex.Bittrex('', '')
        self.private_client = get_private_client()

    @memoize.memoized
    def currencies_df(self):
        """
        
        :return: Dataframe indexed by "Currency" with available currencies. Columns are:
         [u'IsActive', u'TxFee']
        """
        response = self.publict_client.get_currencies()
        result = _to_df(response['result'], 'Currency')
        result = result[['IsActive'], ['TxFee']]
        return result

    @memoize.memoized
    def market_names(self):
        return [r['MarketName'] for r in self.publict_client.get_markets()['result']]

    def get_balances(self):
        """
        bittrex.client returns balances as a list of dictionaries with these keys:
        Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid
        
        :return:  pd.Series that can be used with portfolio.Portfolio(s)
                  It is indexed by "Currency" and has columns Available, Balance, CryptoAddress, Pending, Requested, Uuid
        """
        response = self.private_client.get_balances()
        result = _to_df(response['result'], 'Currency')
        result = result[result['Balance'] > 0]
        result = result['Available']
        return result

    def market_summaries(self):
        """ 
        :return: DataFrame indexed by MarketName with columns: High, Low, Volume, Last, BaseVolume, TimeStamp
        """
        response = self.public_client.get_market_summaries()
        df = _to_df(response['result'], 'MarketName')
        df.drop(['OpenBuyOrders', 'OpenSellOrders', 'PrevDay', 'Bid', 'Ask', 'Created'], axis=1, inplace=True)
        df.loc[:, 'TimeStamp'] = df['TimeStamp'].apply(lambda x: int(parser.parse(x).strftime('%s')))

        return df

    def get_current_market(self):
        """
        bittrex.client returns market_summaries as a list of dictionaries with these keys:
        'Ask', 'BaseVolume', 'Bid', 'Created', 'High', 'Last', 'Low', 'MarketName', 'OpenBuyOrders', 'OpenSellOrders',
         'PrevDay', 'TimeStamp', 'Volume'

        :return:    tuple (timestamp, df)
                    
                    df: pd.Dataframe that can be used with market.Market(df)
                    It is indexed by "MarketName" and has these keys as columns:
                    'Last', 'BaseVolume'
        
        :return: 
        """
        response = self.public_client.get_market_summaries()
        prices_df = _to_df(response['result'], 'MarketName')
        prices_df = prices_df[['Last', 'BaseVolume']]

        timestamp = int(time.time())
        return timestamp, prices_df

    def cancel_all_orders(self):
        response = self.private_client.get_open_orders('')
        for order in response['result']:
            self.private_client.cancel(order['OrderUuid'])

    def withdrawals_and_deposits(self):
        withdrawals = self.private_client.getwithdrawalhistory()
        df = pd.DataFrame()
        for withdrawal in withdrawals['result']:
            s = {'Currencty': withdrawal.get('Currency'),
                 'Address': withdrawal.get('Address'),
                 'Amount': withdrawal.get('Amount'),
                 'Txid': withdrawal.get('TxId'),
                 'TimeStamp': parser.parse(withdrawal.get('Opened')),
                 'Status': withdrawal.get('Status'),
                 'ipAddress': withdrawal.get('ipAddress'),
                 'Type': 'deposit'
            }
            df = df.append(s, ignore_index=True)

        deposits = self.private_client.getdeposithistory()
        for deposit in deposits['result']:
            s = {'Currencty': deposit.get('Currency'),
                 'Address': deposit.get('Address'),
                 'Amount': deposit.get('Amount'),
                 'Txid': deposit.get('TxId'),
                 'TimeStamp': parser.parse(deposit.get('Opened')),
                 'Status': deposit.get('Status'),
                 'ipAddress': deposit.get('ipAddress'),
                 'Type': 'deposit'
                 }
            df = df.append(s, ignore_index=True)

        return df


def get_private_client():
    private_client = None
    if 'BITTREX_KEY_ENCRYPTED' in os.environ:
        # Decrypt code should run once and variables stored outside of the function
        # handler so that these are decrypted once per container
        ENCRYPTED_KEY = os.environ['BITTREX_KEY_ENCRYPTED']
        ENCRYPTED_SECRET = os.environ['BITTREX_SECRET_ENCRYPTED']

        BITTREX_KEY = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_KEY))['Plaintext']
        BITTREX_SECRET = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_SECRET))['Plaintext']
        private_client = bittrex.Bittrex(BITTREX_KEY, BITTREX_SECRET)

    return private_client



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
