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
    fid, filename = tempfile.mkstemp(suffix='{}.csv'.format(timestamp))

    response = bittrex_client.get_market_summaries()
    json_response = json.dumps(response)

    with open(filename, 'w') as fid:
        fid.write(json_response)

    dest_key = hashlib.md5(json_response).hexdigest() + "_" + str(timestamp)
    print('dest_key: {}'.format(dest_key))
    s3_client.upload_file(filename, bucket_name, dest_key)

