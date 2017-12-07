#!/usr/bin/python
"""
I'm following this example from aws documentation

http://docs.aws.amazon.com/lambda/latest/dg/with-scheduled-events.html
"""
from __future__ import print_function
import tempfile
import json
import time

import bittrex_utils
import config

from market import market

bucket_name = 'my-bittrex'


def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


def main():
    import pudb; pudb.set_trace()

    timestamp = int(time.time())

    response = bittrex_utils.client.get_market_summaries()
    json_response = json.dumps(response)

    fid, filename = tempfile.mkstemp(suffix='{}.json'.format(timestamp))
    with open(filename, 'w') as fid:
        fid.write(json_response)

    dest_key = str(timestamp) + '_full'
    #config.s3_client.upload_file(filename, bucket_name, dest_key)

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

    dest_key = str(timestamp) + '_short'
    #config.s3_client.upload_file(filename, bucket_name, dest_key)

    import pudb; pudb.set_trace()

    current_market = market.Market.from_dictionary(short_results, timestamp)
    last = current_market.last_in_usdt(['BTC'])
    volume = current_market.usd_volumes(['BTC'])
    print(last)
    print(volume)


if __name__ == "__main__":
    main()


