from dateutil import parser
import os
import time

from base64 import b64decode
from bittrex import bittrex
import pandas as pd

import config
import memoize
if os.environ['LOGNAME'] == 'aws':
    print('Finished loading', __file__)

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
        response = self.public_client.get_currencies()
        result = _to_df(response['result'], 'Currency')
        result = result[['IsActive', 'TxFee']]
        return result

    @memoize.memoized
    def market_names(self):
        return [r['MarketName'] for r in self.public_client.get_markets()['result']]

    def get_balances(self):
        """
        bittrex.client returns balances as a list of dictionaries with these keys:
        Currency, Balance, CryptoAddress, Pending, Requested, Uuid
        
        :return:  pd.Series that can be used with portfolio.Portfolio(s)
                  It is indexed by "Currency" and has columns, Balance, CryptoAddress, Pending, Requested, Uuid
        """
        response = self.private_client.get_balances()
        result = _to_df(response['result'], 'Currency')
        result = result[result['Balance'] > 0]
        result = result['Balance']
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
        withdrawals = self.private_client.get_withdrawal_history()

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

        deposits = self.private_client.get_deposit_history()
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

    def buy_limit(self, market, quantity, rate):
        result = self.private_client.buy_limit(market, quantity, rate)
        if not result['success']:
            print(result)

    def sell_limit(self, market, quantity, rate):
        result = self.private_client.sell_limit(market, quantity, rate)
        if not result['success']:
            print(result)


    def btc_value(self):
        balance = self.get_balances()
        _, market = self.get_current_market()
        btc = 0
        for currency in balance.index:
            if currency == 'BTC':
                btc += balance[currency]
            else:
                market_name = 'BTC-' + currency
                if market_name in market.index:
                    btc += market.loc[market_name]['Last'] * balance[currency]
        return btc


def get_private_client():
    import pudb; pudb.set_trace()

    if 'BITTREX_KEY_ENCRYPTED' in os.environ:
        # Decrypt code should run once and variables stored outside of the function
        # handler so that these are decrypted once per container
        ENCRYPTED_KEY = os.environ['BITTREX_KEY_ENCRYPTED']
        ENCRYPTED_SECRET = os.environ['BITTREX_SECRET_ENCRYPTED']

        BITTREX_KEY = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_KEY))['Plaintext']
        BITTREX_SECRET = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_SECRET))['Plaintext']

    elif 'BITTREX_KEY' in os.environ:
        # Decrypt code should run once and variables stored outside of the function
        # handler so that these are decrypted once per container
        BITTREX_KEY = os.environ['BITTREX_KEY']
        BITTREX_SECRET = os.environ['BITTREX_SECRET']

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

if os.environ['LOGNAME'] == 'aws':
    print('Finished loading', __file__)
