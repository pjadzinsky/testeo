"""

Download keys from s3 and generate a dataframe with all
the information in them
"""
from itertools import product
import os
import json
import tempfile

import numpy as np
import pandas as pd

import config
from exchanges import exchange
if os.environ['LOGNAME'] == 'aws':
    print('Finished loading', __file__)


bucket = config.s3_client.Bucket('my-bittrex')
CACHED_DIR = os.path.expanduser('~/Testeo/simulations_data/markets/')
try:
    os.makedirs(CACHED_DIR)
except:
    print(('Folder {folder} already exists'.format(folder=CACHED_DIR)))



class Markets(object):
    def __init__(self, seconds, offset, max_markets=10, start_time=None):
        self.seconds = seconds
        self.offset = offset
        self.current_time = None
        self.start_time = start_time
        self.markets = {}
        times = []

        for object in bucket.objects.all():
            if 'short' in object.key:
                timestamp = int(object.key.split('_')[0])
                if start_time and timestamp >= start_time:
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
    def from_dictionary(cls, dictionary, timestamp):
        prices_df = pd.DataFrame(dictionary)
        prices_df.set_index('MarketName', inplace=True)

        return cls(timestamp, prices_df)

    @classmethod
    def at_time(cls, timestamp, max_time_difference):
        for summary in bucket.objects.all():
            if 'short' in summary.key:
                time = int(summary.key.split('_')[0])
                if abs(time - timestamp) < max_time_difference:
                    return cls.from_s3_key(summary.key)

    @classmethod
    def from_s3_key(cls, s3_key):
        _, filename = tempfile.mkstemp(suffix='.csv')
        filename = os.path.join(CACHED_DIR, s3_key)

        timestamp = int(s3_key.split('_')[0])
        if os.path.isfile(filename):
            return cls.from_local_file(filename, timestamp)

        print('Looking and downloading file from s3:', filename)
        if 'short' in s3_key:
            try:
                # object points to a row that we don't have in df, add it
                bucket.download_file(s3_key, filename)
                return cls.from_local_file(filename, timestamp)
            except:
                # quick fix to be able to download file in aws
                _, temp = tempfile.mkstemp()
                bucket.download_file(s3_key, temp)
                return cls.from_local_file(temp, timestamp)


    @classmethod
    def from_exchange(cls):
        timestamp, prices_df = exchange.get_current_market()
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
        
        ie, if A trades with B and B trades with C and you want to know the volume of C in A, then
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
            # no currency trades with itself, volume should be 0 in this case
            return 0
        elif potential_market_name in self.prices_df.index:
            volume = self.prices_df.loc[potential_market_name, 'BaseVolume']
        elif reversed_market_name in self.prices_df.index:
            reversed_market_row = self.prices_df.loc[reversed_market_name]
            volume = reversed_market_row['BaseVolume'] / reversed_market_row['Last']
        else:
            volume = 0

        return self.currency_chain_value(currencies[:-1]) * volume

    def currency_volume(self, base, intermediaries, currencies):
        """ Compute total volume of currencies in base.
        
        a few examples
        1. currency_volume('AAA', ['BBB'], ['CCC', 'DDD'])
         would compute the volume in AAA of both 'CCC' and 'DDD' (going through 'BBB')
         
        2. currency_volume('AAA', ['BBB', 'CCC'], ['DDD'])
         would compute the volume in AAA of 'DDD' (going through both 'BBB' and 'CCC')
         
        3. currency_volume('AAA', [], ['BBB'])
         would compute the volume in AAA of 'BBB'
        
        4. currency_volume('AAA', ['BBB', 'CCC'], ['DDD', 'EEE'])
         would compute the volume in AAA of both 'DDD' and 'EEE' (going through both 'BBB' and 'CCC')
         
        5. currency_volume('AAA', [], Exchange.currencies_df.index)
         computes the volume (in 'AAA') of anything that traded directly with 'AAA'
         
        """
        volume = 0
        assert isinstance(intermediaries, list)
        assert isinstance(currencies, list)

        if base not in intermediaries:
            intermediaries.append(base)

        # 'chains' will be every possible combination between an item in 'intermediaries' and an item in 'currencies'
        chains = product(intermediaries, currencies)
        for chain in chains:
            chain = (base,) + chain
            volume += self.currency_chain_volume(chain)

        return volume

    def usd_volumes(self, intermediates):
        """ Return a dataframe with volumes for all currencies in USDT """
        currencies = exchange.currencies_df().index.values

        volumes = pd.Series([])
        for currency in currencies:
            volumes[currency] = self.currency_volume('USDT', intermediates, [currency])

        volumes.sort_values(ascending=False, inplace=True)
        return volumes

    def last_in_usdt(self, intermediates):
        """ Return a Series index by cryptocurrency where the associated value is the 'Last' traded value but in USDT
        
        For most currencies it is necessary to go through intermediates (which should not include 'USDT')
        Most likely intermediates is just ['BTC']
        """
        if 'USDT' not in intermediates:
            intermediates = ['USDT'] + intermediates

        currencies = exchange.currencies_df().index.values
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

    def base_currencies(self):
        """ Return all currencies that are BaseCurrency for at least one other currency
        BaseCurrency is XXX in a market like XXX-YYY
        """
        all_markets = self.prices_df.index.tolist()
        all_bases = [m.split('-')[0] for m in all_markets]

        # remove duplicates from all_bases
        all_bases = set(all_bases)
        return all_bases

def short_s3_key_from_timestamp(time):
    return "{0}_short".format(time)



if os.environ['LOGNAME'] == 'aws':
    print('Finished loading', __file__)
