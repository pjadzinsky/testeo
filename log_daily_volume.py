#!/usr/bin/python
"""
Simply log current market. It is supposed to run once an hour or so (controlled by lambda)

I'm following this example from aws documentation

http://docs.aws.amazon.com/lambda/latest/dg/with-scheduled-events.html
"""
from __future__ import print_function

import os
import time

import pandas as pd

import market
import s3_utils
from exchanges.exchange import exchange


def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


def main():

    timestamp = int(time.time())

    df_summaries = exchange.market_summaries()

    current_market = market.Market(timestamp, df_summaries[['Last', 'BaseVolume']])

    last = current_market.last_in_usdt(['BTC'])

    if os.environ['EXCHANGE_ACCOUNT'] == 'staging':
        bucket_name = 'exchanges-scratch'
    elif os.environ['EXCHANGE_ACCOUNT'] == 'prod':
        bucket_name = 'exchange-markets'
    else:
        raise IOError("env 'EXCHANGE_ACCOUNT': {} not understood".format(os.environ['EXCHANGE_ACCOUNT']))

    last_dest_key = '{exchange}/markets_lasts.csv'.format(account=os.environ['EXCHANGE'])
    _append(bucket_name, last_dest_key, last, current_market.time)
    volume_dest_key = '{account}/markets_volumes.csv'.format(account=os.environ['EXCHANGE'])
    volume = current_market.usd_volumes(['BTC'])
    _append(bucket_name, volume_dest_key, volume, current_market.time)

    print('Finished')


def _append(bucket_name, s3_key, series, new_index):
    """
    Download df associated with bucket_name and s3_key and add the contents of 'series' 
    as a new column named 'new_index'
    
    :param bucket_name: 
    :param s3_key: 
    :param series: 
    :param new_index: 
    :return: 
    """
    assert type(series) == pd.Series
    df = s3_utils.get_df(bucket_name, s3_key, index_col=0)
    if new_index in df:
        raise ValueError('Dataframe already has this index in it')
    df[new_index] = series
    s3_utils.put_csv(df, bucket_name, s3_key)



if __name__ == "__main__":
    main()

