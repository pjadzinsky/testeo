"""
I'm following this example from aws documentation

http://docs.aws.amazon.com/lambda/latest/dg/with-scheduled-events.html
"""
from __future__ import print_function
import os
import tempfile
import time

from bittrex import bittrex
import boto3
import hashlib
import pandas as pd

import credentials

bucket_name = 'my-bittrex'

s3_client = boto3.client('s3')
bittrex_client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)

def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


def main():
    timestamp = int(time.time())
    print('timestamp: {}'.format(timestamp))
    fid, filename = tempfile.mkstemp(suffix='{}.csv'.format(timestamp))
    print('filename: {}'.format(filename))

    response = bittrex_client.get_market_summaries()
    print('response type: {}'.format(type(response)))
    print('keys: {}'.format(response.keys()))
    print("{}".format(response['result']))
    print('About to call _to_df')
    print('1')
    market = _to_df(response['result'])
    print('2')
    print('market shape: {0}'.format(market.shape))
    market = market[['BaseVolume', 'Last', 'MarketName', 'Volume']]
    print('market type: {}'.format(type(market)))
    print('market shape: {}'.format(market.shape))
    market.loc[:, 'time'] = timestamp
    print('market shape: {}'.format(market.shape))

    market.to_csv(filename)

    dest_key = hashlib.md5(market.to_string()).hexdigest() + "_" + str(timestamp)
    print('dest_key: {}'.format(dest_key))
    s3_client.upload_file(filename, bucket_name, dest_key)


def _to_df(response, new_index=None):
    """
    
    :param summaries: 
    :return: pd.DataFrame: Columns are the keys into each 'summaries'
    
    """
    df = pd.DataFrame([])
    for r in response:
        df = df.append(r, ignore_index=True)
        print('{}'.format(df.shape))

    print('about to return from _to_df')
    return df

