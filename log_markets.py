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

from exchanges.exchange import exchange
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

    df_summaries = exchange.market_summaries()

    fid, filename = tempfile.mkstemp(suffix='{}.json'.format(timestamp))
    df_summaries.to_json(filename)

    bucket = config.s3_client.Bucket(bucket_name)

    dest_key = '{account}/{timestamp}_full'.format(account=os.environ['EXCHANGE_ACCOUNT'], timestamp=timestamp)
    print('uploading {} to {}'.format(filename, dest_key))
    bucket.upload_file(filename, dest_key)



if __name__ == "__main__":
    main()


