import pandas as pd

from bittrex import bittrex
import credentials


client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)
class Test(object):
    def __init__(self, target_state=[]):
        self.target_state = target_state


    def get_ticker(self, currency):
        response = self.client.get_ticker(currency)
        return response

    def rebalance(self):
        """
        Given a state, by/sell positions to approximate target_state
        """
        current = self.client.get_balances()['result']

        print current

    def get_USD_volume(self):
        self.summaries_df.loc[:, 'USD volume'] = self.summaries_df['BaseVolume']

        for base in set(self.summaries_df['Base']):
            try:
                if base == "USDT":
                    base_last = 1
                else:
                    base_last = self.summaries_df.loc['USDT-' + base, 'Last']
                self.summaries_df.loc[self.summaries_df['Base']==base, 'USD volume'] *= base_last
            except:
                self.summaries_df.loc[self.summaries_df['Base']==base, 'USD volume'] = None

        return self.summaries_df[['Currency', 'USD volume']].groupby('Currency').sum().sort_values('USD volume')

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


def summary_by_base_volume():
    summaries = client.get_market_summaries()
    if not summaries['success']:
        raise ValueError(summaries)

    summaries = summaries['result']
    summaries.sort(key=lambda x: -x['BaseVolume'])
    return summaries


def get_currencies():
    response = client.get_currencies()
    if response['success']:
        currencies_df = _to_df(response['result'], 'Currency')

    return currencies_df


def get_summaries():
    response = client.get_market_summaries()
    if response['success']:
        df = _to_df(response['result'], 'MarketName')

    market_name = df.index.values
    base_currency = [mn.split('-') for mn in market_name]
    df.loc[:, 'Base'] = [bc[0] for bc in base_currency]
    df.loc[:, 'Currency'] = [bc[1] for bc in base_currency]

    return df


def get_balances():

    return _to_df(client.get_balances()['result'], 'Currency')


def get_total_balance(base='BTC'):
    """
    Compute the total amount of the portfolio in 'base' curreny
    """
    summaries = get_summaries()
    balances = get_balances()

    # restrict summaries to 'base' currency
    summaries = summaries[summaries.Base==base]

    total = 0
    for currency, series in balances.iterrows():
        market_name = base + "-" + currency
        if currency == base:
            total += series['Balance']
        else:
            total += series['Balance'] * summaries.loc[market_name, 'Last']

    return total

