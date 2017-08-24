"""

Download keys from s3 and generate a dataframe with all
the information in them
"""
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

#gflags.DEFINE_integer('cache_timeout_sec', 3600, 'seconds before downloading all the data from s3 again')
FLAGS = gflags.FLAGS

boto3.setup_default_session(profile_name='user2')
s3_client = boto3.resource('s3')

bucket = s3_client.Bucket('my-bittrex')

cache_file = '/tmp/markets.csv'

class Markets(object):
    def __init__(self, hours, offset):
        self.hours = hours
        self.offset = offset
        self.current_time = None

        # load csv from file
        if os.path.isfile(cache_file):
            if os.stat(cache_file).st_mtime + FLAGS.cache_timeout_sec > time.time():
                df = pd.read_csv(cache_file, index_col=[0, 1])


        _, filename = tempfile.mkstemp(suffix='.csv')
        for object in bucket.objects.all():
            if 'short' in object.key:
                timestamp = int(object.key.split('_')[0])
                if timestamp in df.index.levels[0]:
                    continue

                # object points to a row that we don't have in df, add it
                bucket.download_file(object.key, filename)
                with open(filename, 'r') as fid:
                    temp_df = pd.DataFrame(json.loads(fid.readline()))
                    temp_df.loc[:, 'time'] = timestamp
                    temp_df.set_index(['time', 'MarketName'], inplace=True)

                df = df.append(temp_df)


        df.sort_index(inplace=True)
        self.markets = df
        self.times = df.index.levels[0].tolist()
        df.to_csv(cache_file)


    def market_at_time(self, time):
        """
        markets is a dataframe as returned by get_markets. Has a multiindex (time, MarketName)
        Here we just return the market associated with 'time' dropping one level from the multiindex
        :param markets: 
        :param time: 
        :return: 
        """
        market = None
        if time in self.markets.index.levels[0]:
            market = self.markets.loc[(time, slice(None)), :]
            market.index = market.index.droplevel()
        return market

    def first_market(self):
        first_time = self.markets.index.levels[0].min()
        return self.market_at_time(first_time)

    def last_market(self):
        last_time = self.markets.index.levels[0].max()
        return self.market_at_time(last_time)

    def closest_market(self, time):
        diff = np.array(self.times) - time
        closest_index = np.argmin(diff ** 2)
        closest_time = self.times[closest_index]
        return self.market_at_time(closest_time)

    def __iter__(self):
        return self

    def next(self):
        if not self.current_time:
            self.current_time = self.times[0] + self.offset
        else:
            self.current_time += self.hours

        if self.current_time > self.times[-1]:
            raise StopIteration
        else:
            return self.closest_market(self.current_time)

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
        :param markets: 
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
Now I'm logging markets with log_markets/log_market.py and
log_market/recreate_markets.py loads a DataFrame with a multiindex
(timestamp, MarketName)

All 'market' dataframes below are indexed by just MarketName and are equivalent to
doing
 markets = recreate_markets.get_markets()
 market = recreate_markets(markets, timestamp)
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

    def currency_value(self, currencies):
        """
        Travers currencies (from index 0 to index -1)
        
        ie, if A trades with B and B trades with C and you want to know the price of A in C, then
        currencies = [A, B, C]
        
        currencies: list of str, ie ['BTC', 'USDT']
        """
        if len(currencies) == 0:
            return 0
        elif len(currencies) == 1:
            return 1

        currency = currencies[0]
        base = currencies[1]

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

        return cost * self.currency_value(currencies[1:])

    def _market_name(self,  base, currency):
        return base + "-" + currency

    def usd_volumes(self):
        """ Return a dataframe with volumes for all currencies in USDT """
        currencies = bittrex_utils.currencies_df().index.values

        volumes_df = pd.DataFrame([], columns=['Volume (USDT)'])
        for currency in currencies:
            volumes_df.loc[currency, 'Volume (USDT)'] = self.currency_volume_in_base('USDT', currency)

        volumes_df.sort_values('Volume (USDT)', ascending=False, inplace=True)
        return volumes_df

    def currency_volume_in_base(self, base, intermediates, currency):
        """ Compute total volume of currency in base. Computes the volume of currency when maybe going through
        each intermediate n intermediates.
        
        i.e.
        base = 'AAA'
        intermediates = ['BBB', 'CCC']
        currency = 'DDD'
        
        computes (BaseVolume of BBB-DDD) * (price AAA-BBB) + (BaseVolume of CCC-DDD) * price (AAA-CCC) + 
                 (BaseVolume of AAA-DDD)
        """

        volume = 0
        for intermediate in intermediates:
            name1 = self._market_name(intermediate, currency)
            name2 = self._market_name(base, intermediate)
            if name1 in self.prices_df.index and name2 in self.prices_df.index:
                volume += self.prices_df.loc[name1, 'BaseVolume'] * self.prices_df.loc[name2, 'Last']

        name = self._market_name(base, currency)
        if name in self.prices_df.index:
            volume += self.prices_df.loc[name, 'BaseVolume']

        return volume


    def _direct_volume_in_base(self, base, currency):
        """ Return the volume from market of currency in base. If potential_market_name and/or
        reversed_market_name don't show up in 'market', 0 is returned
        In other words, return the volume of currency in base only if currency and base trade with each other directly,
        ie: base-currency or currency-base is a valid market_name"""
        potential_market_name = self._market_name(base, currency)
        reversed_market_name = self._market_name(currency, base)
        if potential_market_name in self.prices_df.index:
            volume = self.prices_df.loc[potential_market_name, 'BaseVolume']
        elif reversed_market_name in self.prices_df.index:
            volume = self.prices_df.loc[reversed_market_name, 'Volume']
        else:
            volume = 0

        return volume

