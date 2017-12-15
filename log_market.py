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

import bittrex_utils
import config

bucket_name = 'my-bittrex'


def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


def main():
    import pudb; pudb.set_trace()

    timestamp = int(time.time())

    response = bittrex_utils.public_client.get_market_summaries()
    json_response = json.dumps(response)

    fid, filename = tempfile.mkstemp(suffix='{}.json'.format(timestamp))
    with open(filename, 'w') as fid:
        fid.write(json_response)

    dest_key = '{account}/{timestamp}_full'.format(account=os.environ['BITTREX_ACCOUNT'], timestamp=timestamp)
    config.s3_client.upload_file(filename, bucket_name, dest_key)

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


if __name__ == "__main__":
    main()


