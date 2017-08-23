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

gflags.DEFINE_integer('cache_timeout_sec', 24 * 3600, 'seconds before downloading all the data from s3 again')
FLAGS = gflags.FLAGS

boto3.setup_default_session(profile_name='user2')
s3_client = boto3.resource('s3')

bucket = s3_client.Bucket('my-bittrex')

cache_file = '/tmp/markets.csv'

def get_markets():
    if os.path.isfile(cache_file):
        if os.stat(cache_file).st_mtime + FLAGS.cache_timeout_sec > time.time():
            df = pd.read_csv(cache_file, index_col=[0, 1])
            return df

    df = pd.DataFrame([])

    _, filename = tempfile.mkstemp(suffix='.csv')
    for object in bucket.objects.all():
        if 'short' in object.key:
            timestamp = int(object.key.split('_')[0])
            bucket.download_file(object.key, filename)
            with open(filename, 'r') as fid:
                temp_df = pd.DataFrame(json.loads(fid.readline()))
                temp_df.loc[:, 'time'] = timestamp
                temp_df.set_index(['time', 'MarketName'], inplace=True)

            df = df.append(temp_df)

    df.to_csv(cache_file)

    return df


def times():
    markets = get_markets()
    times_list = markets.index.levels[0].tolist()
    times_list.sort()
    return times_list


def market_at_time(time):
    """
    markets is a dataframe as returned by get_markets. Has a multiindex (time, MarketName)
    Here we just return the market associated with 'time' dropping one level from the multiindex
    :param markets: 
    :param time: 
    :return: 
    """
    markets = get_markets()
    market = markets.loc[(time, slice(None)), :]
    market.index = market.index.droplevel()
    return market


def first_market():
    markets = get_markets()
    first_time = markets.index.get_level_values(0).min()
    return market_at_time(first_time)


def last_market():
    markets = get_markets()
    last_time = markets.index.get_level_values(0).max()
    return market_at_time(last_time)


def closest_market(time):
    markets = get_markets()
    times = markets.index.get_level_values(0)
    diff = times - time
    closest = np.argmin(diff ** 2)
    closest_time = times[closest]
    return market_at_time(closest_time)
