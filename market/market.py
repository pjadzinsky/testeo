"""

Download keys from s3 and generate a dataframe with all
the information in them
"""
from itertools import product
import os
import json
import tempfile

import boto3
import numpy as np
import pandas as pd

import bittrex_utils


#boto3.setup_default_session(profile_name='user2')
boto3.setup_default_session()
s3_client = boto3.resource('s3')

bucket = s3_client.Bucket('my-bittrex')
CACHED_DIR = os.path.expanduser('~/Testeo/simulations_data/markets/')
try:
    os.makedirs(CACHED_DIR)
except:
    print ('Folder {folder} already exists'.format(folder=CACHED_DIR))



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
        # market will be None if not in self.markets dictionary
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
            # TODO Make it lazy. Looping should not open the csv until the market needs to be used
            market = self.closest_market(self.current_time)
            self.current_time = market.time

            return market

    def reset(self, current_time=None, seconds=None):
        """
        Will cause iterator to start over
        :return: 
        """
        # if current_time is None, this is fine. ON first iteration it is set to the first time available
        self.current_time = current_time

        if seconds:
            self.seconds = seconds

    def stats_volume(self):
        """
        Compute some estimate of variance
        :param market: 
        :return: 
        """
        self.reset()
        volume_df = pd.DataFrame([])
        for market in self:
            t = market.time
            volume_df[t] = market.usd_volumes(['BTC'])['Volume (USDT)']

        volume_df = volume_df.mean(axis=1)

        volume_df.columns = ['Volume (USDT)']
        volume_df.sort_values(ascending=False, inplace=True)
        return volume_df

    def rollling_variance(self, hours):
        """
        Compute the variance in USDT as a function of time for each cryptocurrency.
        :param hours: 
        :return: 
        """
        # first concatenate all the 'Last' prices in last_df. Index is market_name and columns are 'time_sec'
        last_df = pd.DataFrame([])
        for market in self:
            t = market.time
            last_df[t] = market.prices_df['Last']


    def stats_variance(self, window):
        """
        Compute some estimate of variance
        :param window: pd.rolling window parameter
        :return: 
        """
        self.reset()
        variance_df = pd.DataFrame([])
        for market in self:
            t = market.time
            variance_df[t] = market.last_in_usdt(['BTC'])

        t = variance_df.T
        # TODO 12 points, points are one hour apart but this should be checked since it can change
        rolling = t.rolling(window)

        mean_df = rolling.mean()
        std_df = rolling.std()
        percentual_std_df = std_df / mean_df
        percentual_std_df.dropna(how='all', inplace=True)
        return percentual_std_df

    def mean_variance(self, start, end):
        """
        Idea was to compute mean of output of stats_vaariance only taking into account simulations_code in between
        start and end.
        
        Need better time control in markets, so that iteration will stop if time > end
        :param start: 
        :param end: 
        :return: 
        """
        self.reset(start)

        variances_df = stats_variance


class Market(object):
    def __init__(self, time, prices_df):
        self.time = time
        self.prices_df = prices_df

    @classmethod
    def from_local_file(cls, filename, timestamp):
        assert os.path.isfile(filename)
        with open(filename, 'r') as fid:
            prices_df = pd.DataFrame(json.loads(fid.readline()))
            prices_df.set_index('MarketName', inplace=True)

        return cls(timestamp, prices_df)

    @classmethod
    def from_s3_key(cls, s3_key):
        _, filename = tempfile.mkstemp(suffix='.csv')
        filename = os.path.join(CACHED_DIR, s3_key)

        timestamp = int(s3_key.split('_')[0])
        if os.path.isfile(filename):
            return cls.from_local_file(filename, timestamp)

        print 'Looking and downloading file from s3:', filename
        if 'short' in s3_key:
            # object points to a row that we don't have in df, add it
            bucket.download_file(s3_key, filename)
            return cls.from_local_file(filename, timestamp)

    @classmethod
    def from_bittrex(cls):
        print 'A'
        timestamp, prices_df = bittrex_utils.get_current_market()
        print 'B'
        return cls(timestamp, prices_df)

    def _market_name(self,  base, currency):
        return base + "-" + currency

    def currency_chain_value(self, currencies):
        """
        Travers currencies (from currencies[-1] to currencies[0])
        
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

    def last_in_usdt(self, intermediates):
        """ Return a Series index by cryptocurrency where the associated value is the 'Last' traded value but in USDT
        
        For most currencies it is necessary to go through inermediates (which should not include 'USDT')
        Most likely intermediates is just ['BTC']
        """
        if 'USDT' not in intermediates:
            intermediates = ['USDT'] + intermediates

        currencies = bittrex_utils.currencies_df().index.values
        values = [self.currency_chain_value(intermediates + [c]) for c in currencies]

        s = pd.Series(values, index=currencies)
        return s

    def inconsistencies(self):
        """
        Return a pd.Dataframe with the 'Last price in 'USDT' when going through BTC and ETH for every currency
        
        :return: 
        """
        s_eth = self.last_in_usdt(['ETH'])
        s_btc = self.last_in_usdt(['BTC'])

        df = pd.DataFrame([])
        df.loc[:, 'Through ETH'] = s_eth
        df.loc[:, 'Through BTC'] = s_btc
        df.loc[:, 'diff'] = df.max(axis=1) - df.min(axis=1)
        df.sort_values('diff', ascending=False, inplace=True)
        return df


def short_s3_key_from_timestamp(time):
    return "{0}_short".format(time)


def pick_markets(N, markets_distance, rolling_window_size):
    """
    
    :param N: Number of currencies to return
    :param markets_distance: distsance in seconds in between market conditions used
    :param rolling_window_size: How many points to take into accouont when computing volume and variance.
                                Total time considered is rolling_window_size * markets_distance
    :return: 
    """
    markets = Markets(markets_distance, 0)

    volumes = markets.stats_volume()
    print '*' * 80
    print 'market volumes'
    print volumes.head(20)

    variance_df = markets.stats_variance(rolling_window_size)
    mean_variance = variance_df.mean(axis=0)

    mean_variance.sort_values(ascending=False, inplace=True)
    print mean_variance.head(20)
    print mean_variance.index.values[:30]
    print '*' * 80

    print type(volumes), type(mean_variance)
    df = pd.concat([volumes, mean_variance], axis=1)
    df.columns = ['volume', 'variance']
    df = df[df['volume'] > 1E6]
    df = df.sort_values('variance', ascending=False)
    print ','.join(df.index.values[:N])
    return df.index.values[:N]

