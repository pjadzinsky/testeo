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
        response = self.public_client.returnCurrencies()
        result = _to_df(response)

        result.loc[:, 'IsActive'] = ~ result['disabled'].astype(bool)
        result = result[['IsActive', 'txFee']]
        result.columns = ['IsActive', 'TxFee']
        return result

    @memoize.memoized
    def market_names(self):

        response = self.public_client.returnTicker()
        answer = response.keys()

        if os.environ['EXCHANGE'] == 'POLONIEX':
            answer = [a.replace('_', '-') for a in answer]

        return answer


    def get_balances(self):
        """
        poloniex.client returns balances as a dictionary linking cryptocurrency to amount, nothing more
        
        :return:  pd.Series
        """
        response = self.private_client.returnBalances()
        s = pd.Series(response.values(), index=response.keys())
        s = s[s > 0]
        s.name = 'Available'
        s.index.name = 'Currency'

        return s


    def market_summaries(self):
        """ 
        :return: DataFrame indexed by MarketName with columns: High, Low, Volume, Last, BaseVolume, TimeStamp
        """
        # TODO seems like I should be subscribing to the PUSH API rather than doing this
        response = self.public_client.returnTicker()
        ticker_df = _to_df(response)
        high = [None] * len(ticker_df)
        low = high
        volume = ticker_df['quoteVolume']
        last = ticker_df['last']
        base_volume = ticker_df['baseVolume']
        timestamp = int(time.time())
        market_pairs = ticker_df.index

        df = pd.DataFrame({'High': high, 'Low': low, 'Volume': volume, 'Last': last, 'BaseVolume': base_volume,
                           'TimeStamp': timestamp}, index=market_pairs)

        return df

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
        response = self.public_client.returnTicker()
        prices_df = _to_df(response)
        prices_df = prices_df[['last', 'baseVolume']]
        prices_df.columns = ['Last', 'BaseVolume']
        prices_df.index.name = 'MarketName'

        timestamp = int(time.time())
        return timestamp, prices_df

    def cancel_all_orders(self):
        response = self.private_client.returnOpenOrders()
        for currency_pair, orders in response.items():
            for order in orders:
                id = order['orderNumber']
                status = self.private_client.cancelOrder(id)
                if not status['success']:
                    print 'currency_pair', order, id, 'failed to cancel'

    def withdrawals_and_deposits(self):
        start = 151000000
        end = time.time()
        response = self.private_client.returnDepositsWithdrawals(start, end)
        df = pd.DataFrame()
        for withdrawal_flag, transactions in response.items():
            for transaction in transactions:
                s = {'Currencty': transaction.get('currency'),
                     'Address': transaction.get('address'),
                     'Amount': transaction.get('amount'),
                     'Txid': transaction.get('txid'),
                     'TimeStamp': transaction.get('timestamp'),
                     'Status': transaction.get('status'),
                     'ipAddress': transaction.get('ipAddress'),
                     'Type': withdrawal_flag.rstrip('s')
                }

                df = df.append(s, ignore_index=True)

        return df

    def buy_limit(self, market, quantity, rate):
        try:
            self.private_client.buy(market.replace('-', '_'), rate, quantity)
        except:
            self.private_client.buy(market.replace('-', '_'), rate, quantity * 0.9)


    def sell_limit(self, market, quantity, rate):
        self.private_client.sell(market.replace('-', '_'), rate, quantity)

    def btc_value(self):
        balances = self.private_client.returnCompleteBalances()
        # only keep items with positive balance
        balances = {k: v for k, v in balances.items() if v['available']}

        # now keep only the approximated value in bitcoins
        btcs = [d['btcValue'] for d in balances.values()]

        return sum(btcs)


def get_private_client():
    if 'POLONIEX_KEY_ENCRYPTED' in os.environ:
        # Decrypt code should run once and variables stored outside of the function
        # handler so that these are decrypted once per container
        ENCRYPTED_KEY = os.environ['POLONIEX_KEY_ENCRYPTED']
        ENCRYPTED_SECRET = os.environ['POLONIEX_SECRET_ENCRYPTED']

        POLONIEX_KEY = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_KEY))['Plaintext']
        POLONIEX_SECRET = config.kms_client.decrypt(CiphertextBlob=b64decode(ENCRYPTED_SECRET))['Plaintext']

    elif 'POLONIEX_KEY' in os.environ:
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
        # poloniex uses XXX_YYY and my code assumes in several places XXX-YYY. For the time being I'm changing
        # the key from XXX_YYY into XXX-YYY
        row = pd.Series(v.values(), index=v.keys(), name=k.replace('_', '-'))

        df = df.append(row)

    return df

print 'finished loading', __file__
