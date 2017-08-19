"""
I'm following this example from aws documentation

http://docs.aws.amazon.com/lambda/latest/dg/with-scheduled-events.html
"""
from __future__ import print_function
import tempfile
import json
import time

from bittrex import bittrex
import boto3
import hashlib

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

    response = bittrex_client.get_market_summaries()
    json_response = json.dumps(response)

    fid, filename = tempfile.mkstemp(suffix='{}.json'.format(timestamp))
    with open(filename, 'w') as fid:
        fid.write(json_response)

    dest_key = str(timestamp) + '_full'
    s3_client.upload_file(filename, bucket_name, dest_key)

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
    s3_client.upload_file(filename, bucket_name, dest_key)

if __name__ == "__main__":
    main()


