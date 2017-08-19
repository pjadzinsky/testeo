"""
Originally coded in my_bittrex.volume as a class.
Now I'm logging markets with log_markets/log_market.py and
log_market/recreate_markets.py loads a DataFrame with a multiindex
(timestamp, MarketName)

All 'market' dataframes below are indexed by just MarketName and are equivalent to
doing
 markets = recreate_markets.get_markets()
 market = recreate_markets(markets, timestamp)
"""
import pandas as pd

import bittrex_utils

def currency_value(market, currencies):
    """
    Travers currencies (from index 0 to index -1)
    
    ie, if A trades with B and B trades with C and you want to know the price of A in C, then
    currencies = [A, B, C]
    """
    if len(currencies) == 0:
        return 0
    elif len(currencies) == 1:
        return 1

    currency = currencies[0]
    base = currencies[1]

    potential_market_name = _market_name(base, currency)
    reversed_market_name = _market_name(currency, base)
    if currency == base:
        cost = 1.0
    elif potential_market_name in market.index:
        cost = market.loc[potential_market_name, 'Last']
    elif reversed_market_name in market.index:
        cost = 1.0 / market.loc[reversed_market_name, 'Last']
    else:
        cost = 0

    return cost * currency_value(market, currencies[1:])


def _market_name( base, currency):
    return base + "-" + currency


def usd_volumes(market):
    """ Return a dataframe with volumes for all currencies in USDT """
    currencies = bittrex_utils.currencies_df().index.values

    volumes_df = pd.DataFrame([], columns=['Volume (USDT)'])
    for currency in currencies:
        volumes_df.loc[currency, 'Volume (USDT)'] = currency_volume_in_base(market, 'USDT', currency)

    volumes_df.sort_values('Volume (USDT)', ascending=False, inplace=True)
    return volumes_df


def currency_volume_in_base(market, base, currency):
    """ Comute total volume of currency in either BTC, ETH or USDT """
    assert base in ['BTC', 'ETH', 'USDT']

    if base == 'BTC':
        return _volume_in_btc(market, currency)
    elif base == 'ETH':
        return _volume_in_eth(market, currency)
    elif base == 'USDT':
        return _volume_in_usdt(market, currency)
    else:
        raise IOError

def _volume_in_btc(market, currency):
    """ Compute the total volume of currency in BTC
    """
    usdt_vol = _direct_volume_in_base(market, 'USDT', currency)
    eth_vol = _direct_volume_in_base(market, 'ETH', currency)
    btc_vol = _direct_volume_in_base(market, 'BTC', currency)

    btc_vol += eth_vol * currency_value(market, ['ETH', 'BTC']) + usdt_vol * currency_value(market, ['USDT', 'BTC'])
    return btc_vol


def _volume_in_eth(market, currency):
    """ Compute the total volume of currency in ETH
    """
    usdt_vol = _direct_volume_in_base(market, 'USDT', currency)
    eth_vol = _direct_volume_in_base(market, 'ETH', currency)
    btc_vol = _direct_volume_in_base(market, 'BTC', currency)

    eth_vol += btc_vol * currency_value(market, ['BTC', 'ETH']) + usdt_vol * currency_value(market, ['USDT', 'ETH'])
    return eth_vol


def _volume_in_usdt(market, currency):
    """ Compute the total volume of currency in ETH
    """
    usdt_vol = _direct_volume_in_base(market, 'USDT', currency)
    eth_vol = _direct_volume_in_base(market, 'ETH', currency)
    btc_vol = _direct_volume_in_base(market, 'BTC', currency)

    usdt_vol += btc_vol * currency_value(market, ['BTC', 'USDT']) + eth_vol * currency_value(market, ['ETH', 'USDT'])
    return usdt_vol


def _direct_volume_in_base(market, base, currency):
    """ Return the volume from market of currency in base. If potential_market_name and/or
    reversed_market_name don't show up in market 0 is returned
    In other words, return the volume of currency in base only if currency and base trade with each other directly,
    ie: base-currency or currency-base is a valid market_name"""
    potential_market_name = _market_name(base, currency)
    reversed_market_name = _market_name(currency, base)
    if potential_market_name in market.index:
        volume = market.loc[potential_market_name, 'BaseVolume']
    elif reversed_market_name in market.index:
        volume = market.loc[reversed_market_name, 'Volume']
    else:
        volume = 0

    return volume


