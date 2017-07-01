import pandas as pd

from bittrex import bittrex
from tensorflow.contrib.layers.python.layers import summaries

import credentials


client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)
class Portfolio(object):
    def __init__(self, target_state):
        self.target_state = target_state


    def get_ticker(self, currency):
        response = self.client.get_ticker(currency)
        return response

    def rebalance(self):
        """
        Given a state, by/sell positions to approximate target_state
        """
        current = self.client.get_balances()['result']


def get_USD_volume():
    summaries = get_summaries()
    summaries.loc[:, 'USD volume'] = summaries['BaseVolume']

    for base in set(summaries['Base']):
        try:
            if base == "USDT":
                base_last = 1
            else:
                base_last = summaries.loc['USDT-' + base, 'Last']
            summaries.loc[summaries['Base']==base, 'USD volume'] *= base_last
        except:
            summaries.loc[summaries['Base']==base, 'USD volume'] = None

    return summaries[['Currency', 'USD volume']].groupby('Currency').sum().sort_values('USD volume')


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


def get_currencies():
    """
    
    :return: Dataframe indexed by "Currency" with available currencies
    """
    response = client.get_currencies()
    if response['success']:
        currencies_df = _to_df(response['result'], 'Currency')

    return currencies_df


def get_summaries():
    """
    :return: Dataframe indexed by "MarketName" with market data about each urrency
    """
    response = client.get_market_summaries()
    if response['success']:
        df = _to_df(response['result'], 'MarketName')

    # it becomes simpler later on if we treat USDT as another crypto-currency
    # treated in BTC and ETH as anything else
    df = df.append(_invert_base(df.loc['USDT-ETH']))
    df = df.append(_invert_base(df.loc['USDT-BTC']))


    market_name = df.index.values
    base_currency = [mn.split('-') for mn in market_name]
    df.loc[:, 'Base'] = [bc[0] for bc in base_currency]
    df.loc[:, 'Currency'] = [bc[1] for bc in base_currency]

    return df


def get_balances():
    """
    
    :return: Dataframe indexed by 'Currency' with our portfolio
    """
    df = _to_df(client.get_balances()['result'], 'Currency')
    if df.empty:
        df = pd.read_csv('balances.csv')

    return df


def get_total_balance(base='BTC'):
    """
    Compute the total amount of the portfolio in 'base' currency ('ETH' and 'BTC' for the time being but not USDT)
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


def start_new_porfolio(N, base_currency, value):
    """
    Start a new blanace out of the N crypto currencies with more volume
    balanced is generated as a DF and stored as a csv under
    'balance.csv'
    
    :param N: number of cryptocurrencies to use.
    :param base_currency: str, currency we are funding the portfolio with ('ETH' or 'BTC')
    :param value: float, initial value of portfolio in 'base_currency'
    :return: 
    """
    summaries = get_summaries()
    volume = get_USD_volume().tail(N)
    currencies = volume.index.values.tolist()
    market_names = _market_names(volume, base_currency)
    balances = value / summaries.loc[market_names, 'Last'].values / N

    df = pd.DataFrame({
        "Currency": currencies,
        "Balance" : balances,
        "Available" : balances,
        "Pending" : [0] * N,
        "CryptoAddress" : ["DLxcEt3AatMyr2NTatzjsfHNoB9NT62HiF"] * N,
        "Requested" : [False] * N,
        "Uuid" : [None] * N
        })

    df.set_index('Currency', drop=True, inplace=True)
    df.to_csv('balances.csv')

    return df


def _invert_base(summary_row):
    """
    Invert the relationshipt between Base and Currency for a given
    row of summary
    
    :param summary_row: 
    :return: series with same index as summary_row
    """
    output = summary_row.copy()
    output['Ask'] = 1.0 / summary_row['Ask']
    output['BaseVolume'] = summary_row['BaseVolume'] / summary_row['Last']
    output['Bid'] = 1.0 / summary_row['Bid']
    output['Created'] = summary_row['Created']
    output['High'] = 1.0 / summary_row['Low']
    output['Last'] = 1.0 / summary_row['Last']
    output['Low'] = 1.0 / summary_row['High']
    output['OpenBuyOrders'] = summary_row['OpenSellOrders']
    output['OpenSellOrders'] = summary_row['OpenBuyOrders']
    output['PrevDay'] = 1.0 / summary_row['PrevDay']
    output['TimeStamp'] = summary_row['TimeStamp']
    output['Volume'] = summary_row['Volume']
    if 'Currency' in summary_row:
        output['Base'] = summary_row['Currency']
    if 'Base' in summary_row:
        output['Currency'] = summary_row['Base']

    # new MarketName
    new_currency, new_base = summary_row.name.split('-')
    output.rename(new_base + '-' + new_currency, inplace=True)
    return output

def _market_names(df, base_currency):
    """
    :param df: DataFrame indexed by 'currency'
    :param base_currency: str, base currency
    :return: list of strings of the form base-currency_1, base-currency2, etc
    """

    currencies = df.index.values.tolist()
    return [base_currency + "-" + c for c in currencies]
