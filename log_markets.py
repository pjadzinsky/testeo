#!/usr/bin/python
"""
Simply log current market. It is supposed to run once an hour or so (controlled by lambda)

I'm following this example from aws documentation

http://docs.aws.amazon.com/lambda/latest/dg/with-scheduled-events.html
"""
from __future__ import print_function
import os
import tempfile
import time

from exchanges.exchange import exchange
import s3_utils
import config



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

    bucket = s3_utils.get_write_bucket(config.MARKETS_BUCKET)

    dest_key = '{exchange}/{timestamp}'.format(exchange=os.environ['EXCHANGE'],
                                               timestamp=timestamp)
    print('uploading {} to {}'.format(filename, dest_key))
    bucket.upload_file(filename, dest_key)


if __name__ == "__main__":
    main()


