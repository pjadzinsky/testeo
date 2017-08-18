#!/usr/bin/python
"""

Download keys from s3 and generate a dataframe with all
the information in them
"""
import os
import json
import tempfile

import boto3
import pandas as pd

boto3.setup_default_session(profile_name='user2')
s3_client = boto3.resource('s3')

bucket = s3_client.Bucket('my-bittrex')


def get_markets():
    df = pd.DataFrame([])

    _, filename = tempfile.mkstemp(suffix='.csv')
    for object in bucket.objects.all():
        if 'short' in object.key:
            timestamp = int(object.key.split('_')[0])
            bucket.download_file(object.key, filename)
            with open(filename, 'r') as fid:
                temp_df = pd.DataFrame(json.loads(fid.readline()))
                temp_df.loc[:, 'time'] = timestamp
                temp_df.set_index(['time', 'MarketName'], inplace=True)

            df = df.append(temp_df)

    print df.shape
    print df.head()
    print df.tail()
    return df




if __name__ == "__main__":
    get_markets()
