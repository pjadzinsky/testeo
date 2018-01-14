#!/usr/bin/python
import hashlib
import os
import tempfile
import time

import boto3

from trash.my_bittrex import volume

portfolio_csv = os.path.join('data', 'portfolio.csv')
market_csv = os.path.join('data', 'market.csv')
bucket_name = 'my-bittrex'

s3_client = boto3.client('s3')

def main():
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'
    while True:
        timestamp = int(time.time())
        fid, filename = tempfile.mkstemp(suffix='{}.csv'.format(timestamp))

        market = volume.Market()
        last = market.summaries()['Last']
        last['time'] = timestamp

        last.to_csv(filename)

        dest_key = hashlib.md5(last.to_string()).hexdigest() + "_" + str(timestamp)
        s3_client.upload_file(filename, bucket_name, dest_key)

        break
        time.sleep(600)


if __name__ == "__main__":
    main()
