"""

Download keys from s3 and generate a dataframe with all
the information in them
"""
from itertools import product
import os
import json
import tempfile
import time

import boto3
import gflags
import numpy as np
import pandas as pd

import bittrex_utils
import memoize

FLAGS = gflags.FLAGS

boto3.setup_default_session(profile_name='user2')
s3_client = boto3.resource('s3')

bucket = s3_client.Bucket('my-bittrex')


class Markets(object):
    def __init__(self, seconds, offset, max_markets=10):
        self.seconds = seconds
        self.offset = offset
        self.current_time = None
        self.markets = {}
        times = []

        for object in bucket.objects.all():
            if 'short' in object.key:
                timestamp = int(object.key.split('_')[0])
                times.append(timestamp)

        times.sort()
        self.times = times

    def market_at_time(self, time):
        """
        market is a dataframe as returned by get_markets. Has a multiindex (time, MarketName)
        Here we just return the market associated with 'time' dropping one level from the multiindex
        :param time: 
        :return: 
        """
        # market will be None if not in self.market dictionary
        market = self.markets.get(time)
        if not market:
            if time in self.times:
                market = Market.from_s3_key(short_s3_key_from_timestamp(time))

        return market

    def first_market(self):
        print self.times[0]
        return self.market_at_time(self.times[0])

    def last_market(self):
        return self.market_at_time(self.times[-1])

    def closest_market(self, time):
        diff = np.array(self.times) - time
        closest_index = np.argmin(diff ** 2)
        return self.market_at_time(self.times[closest_index])

    def __iter__(self):
        return self

    def next(self):
        if not self.current_time:
            self.current_time = self.times[0] + self.offset
        else:
            self.current_time += self.seconds

        if self.current_time > self.times[-1]:
            raise StopIteration
        else:
            return self.current_time, self.closest_market(self.current_time)

    def variance(self):
        """
        Compute some estimate of variance
        :param market: 
        :return: 
        """
        market_names = self.markets.index.levels[1]
        variances_df = pd.DataFrame([])
        for name in market_names:
            market = self.markets.loc[(slice(None), name), :]
            variances_df.loc[name, 'Var'] = market['Last'].var()

        variances_df.sort_values('Var', ascending=False, inplace=True)
        return variances_df

    def volume(self, ascending=False):
        """
        Compute average market size
        :param market: 
        :return: 
        """
        market_names = self.markets.index.levels[1]
        volumes_df = pd.DataFrame([])
        for name in market_names:
            market = self.markets.loc[(slice(None), name), :]
            mean = market.mean()
            mean.name = name
            volumes_df = volumes_df.append(mean)

        volumes_df.sort_values('BaseVolume', ascending=ascending, inplace=True)
        return volumes_df

"""
Originally coded in my_bittrex.volume as a class.
Now I'm logging market with log_markets/log_market.py and
log_market/market.py loads a DataFrame with a multiindex
(timestamp, MarketName)

All 'market' dataframes below are indexed by just MarketName and are equivalent to
doing
 market = recreate_markets.get_markets()
 market = recreate_markets(market, timestamp)
"""

class Market(object):
    def __init__(self, time, prices_df):
        self.time = time
        self.prices_df = prices_df

    @classmethod
    @memoize.memoized
    def from_s3_key(cls, s3_key):
        _, filename = tempfile.mkstemp(suffix='.csv')
        prices_df = None
        if 'short' in s3_key:
            timestamp = int(s3_key.split('_')[0])

            # object points to a row that we don't have in df, add it
            bucket.download_file(s3_key, filename)
            with open(filename, 'r') as fid:
                prices_df = pd.DataFrame(json.loads(fid.readline()))
                prices_df.set_index('MarketName', inplace=True)

            return cls(timestamp, prices_df)

    def _market_name(self,  base, currency):
        return base + "-" + currency

    def currency_chain_value(self, currencies):
        """
        Travers currencies (from index -1 to index 0)
        
        ie, if A trades with B and B trades with C and you want to know the price of C in A, then
        currencies = [A, B, C]
        
        currencies: list of str, ie ['USDT', 'BTC']
        """
        if len(currencies) == 0:
            return 0
        elif len(currencies) == 1:
            return 1

        currency = currencies[-1]
        base = currencies[-2]

        potential_market_name = self._market_name(base, currency)
        reversed_market_name = self._market_name(currency, base)
        if currency == base:
            cost = 1.0
        elif potential_market_name in self.prices_df.index:
            cost = self.prices_df.loc[potential_market_name, 'Last']
        elif reversed_market_name in self.prices_df.index:
            cost = 1.0 / self.prices_df.loc[reversed_market_name, 'Last']
        else:
            cost = 0

        return cost * self.currency_chain_value(currencies[:-1])

    def currency_chain_volume(self, currencies):
        """
        Travers currencies (from index -1 to index 0)
        
        ie, if A trades with B and B trades with C and you want to know the price of C in A, then
        currencies = [A, B, C]
        
        currencies: list of str, ie ['USDT', 'BTC']
        """

        if len(currencies) <= 1:
            return 0

        currency = currencies[-1]
        base = currencies[-2]

        potential_market_name = self._market_name(base, currency)
        reversed_market_name = self._market_name(currency, base)

        if currency == base:
            return 0
        elif potential_market_name in self.prices_df.index:
            volume = self.prices_df.loc[potential_market_name, 'BaseVolume']
        elif reversed_market_name in self.prices_df.index:
            volume = self.prices_df.loc[reversed_market_name, 'Volume']
        else:
            volume = 0

        return self.currency_chain_value(currencies[:-1]) * volume

    def currency_volume(self, base, list_of_intermediates):
        """ Compute total volume of currency in base.
        
        list_of_intermediates is a list of lists
        a few examples
        1. currency_volume('AAA', [['BBB'], ['CCC', 'DDD']])
         would compute the volume in AAA of both 'CCC' and 'DDD' (going through 'BBB')
         
        2. currency_volume('AAA', [['BBB', 'CCC'], ['DDD']])
         would compute the volume in AAA of 'DDD' (going through both 'BBB' and 'CCC')
         
        3. currency_volume('AAA', [['BBB']]
         would compute the volume in AAA of 'BBB'
        
        4. currency_volume('AAA', [['BBB', 'CCC'], ['DDD', 'EEE']])
         would compute the volume in AAA of both 'DDD' and 'EEE' (going through both 'BBB' and 'CCC')
         
        5. currency_volume('AAA', [[]])
            special case, computes the volume (in 'AAA') of anything that traded directly with 'AAA'
         
        """
        volume = 0

        if len(list_of_intermediates[0]) == 0:
            list_of_intermediates = [bittrex_utils.currencies_df().index.tolist()]

        chains = product(*list_of_intermediates)
        for chain in chains:
            chain = (base,) + chain
            volume += self.currency_chain_volume(chain)

        return volume

    def usd_volumes(self, intermediates):
        """ Return a dataframe with volumes for all currencies in USDT """
        currencies = bittrex_utils.currencies_df().index.values

        volumes_df = pd.DataFrame([], columns=['Volume (USDT)'])
        for currency in currencies:
            volumes_df.loc[currency, 'Volume (USDT)'] = self.currency_volume('USDT', [intermediates, [currency]])

        volumes_df.sort_values('Volume (USDT)', ascending=False, inplace=True)
        return volumes_df

def short_s3_key_from_timestamp(time):
    return "{0}_short".format(time)
