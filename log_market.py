#!/usr/bin/python
"""
Simply log current market. It is supposed to run once an hour or so (controlled by lambda)

I'm following this example from aws documentation

http://docs.aws.amazon.com/lambda/latest/dg/with-scheduled-events.html
"""
from __future__ import print_function
import json
import os
import tempfile
import time

import pandas as pd

import bittrex_utils
import config
from market import market
import s3_utils

bucket_name = 'my-bittrex'


def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


def main():

    timestamp = int(time.time())

    response = bittrex_utils.public_client.get_market_summaries()
    json_response = json.dumps(response)

    fid, filename = tempfile.mkstemp(suffix='{}.json'.format(timestamp))
    with open(filename, 'w') as fid:
        fid.write(json_response)

    bucket = config.s3_client.Bucket(bucket_name)

    dest_key = '{account}/{timestamp}_full'.format(account=os.environ['BITTREX_ACCOUNT'], timestamp=timestamp)
    bucket.upload_file(filename, dest_key)

    result = response['result']
    short_results = []
    for r in result:
        del r["PrevDay"]
        del r["TimeStamp"]
        del r["Bid"]
        del r["Created"]
        del r["OpenBuyOrders"]
        del r["OpenSellOrders"]
        del r["High"]
        del r["Low"]
        del r["Ask"]
        short_results.append(r)

    fid, filename = tempfile.mkstemp(suffix='{}.json'.format(timestamp))
    print(filename)
    with open(filename, 'w') as fid:
        fid.write(json.dumps(short_results))

    dest_key = '{account}/{timestamp}_short'.format(account=os.environ['BITTREX_ACCOUNT'], timestamp=timestamp)
    bucket.upload_file(filename, dest_key)

    current_market = market.Market.from_dictionary(short_results, timestamp)
    last = current_market.last_in_usdt(['BTC'])

    last_dest_key = '{account}/markets_lasts.csv'.format(account=os.environ['BITTREX_ACCOUNT'])
    append(bucket_name, last_dest_key, last, timestamp)
    volume_dest_key = '{account}/markets_volumes.csv'.format(account=os.environ['BITTREX_ACCOUNT'])
    volume = current_market.usd_volumes(['BTC'])
    append(bucket_name, volume_dest_key, volume, timestamp)


def append(bucket_name, s3_key, row, new_index):
    df = s3_utils.get_df(bucket_name, s3_key, index_col=0)
    df[new_index] = row
    s3_utils.put_csv(df, bucket_name, s3_key)



if __name__ == "__main__":
    main()


