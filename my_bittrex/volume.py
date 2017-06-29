import pandas as pd

from bittrex import bittrex
import credentials


class Test(object):
    client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)

    def get_currencies(self):
        response = self.client.get_currencies()
        if response['success']:
            self.currencies_df = self._to_df(response['result'])

        self.currencies_df.set_index('Currency', drop=True, inplace=True)

    def get_ticker(self):
        response = self.client.get_ticker()

    def get_summaries(self):
        response = self.client.get_market_summaries()
        if response['success']:
            df = self._to_df(response['result'])

        df.loc[:, 'Base'] = df['MarketName'].apply(lambda x: x.split('-')[0])
        df.loc[:, 'Currency'] = df['MarketName'].apply(lambda x: x.split('-')[1])
        df.set_index('MarketName', drop=True, inplace=True)

        self.summaries_df = df

    def get_USD_volume(self):
        self.summaries_df.loc[:, 'USD volume'] = self.summaries_df['BaseVolume']

        for base in set(self.summaries_df['Base']):
            try:
                base_last = self.summaries_df.loc['USDT-' + base, 'Last']
                self.summaries_df.loc[self.summaries_df['Base']==base, 'USD volume'] *= base_last
            except:
                self.summaries_df.loc[self.summaries_df['Base']==base, 'USD volume'] = None


    def _to_df(self, response):
        """
        
        :param summaries: 
        :return: pd.DataFrame: Columns are the keys into each 'summaries'
        
        """
        df = pd.DataFrame([])
        for r in response:
            df = df.append(r, ignore_index=True)

        return df


def summary_by_base_volume():
    summaries = client.get_market_summaries()
    if not summaries['success']:
        raise ValueError(summaries)

    summaries = summaries['result']
    summaries.sort(key=lambda x: -x['BaseVolume'])
    return summaries




def currency_by_USD_volume():
    """
    Each currency might be traded against several other currencies. Sum the total
    traded volume in USD and return a dictionary with Ticker: Volume (USD) values
    """
    summaries = client.get_market_summaries()
    if not summaries['success']:
        raise ValueError(summaries)

    summaries = summaries['result']
    summaries.sort(key=lambda x: -x['BaseVolume'])
    return summaries
