import json
import os
import tempfile
import re

import pandas as pd

import config

def log_df(bucket_name, s3_key, some_df):
    if os.environ['PORTFOLIO_REPORT']:
        bucket = config.s3_client.Bucket(bucket_name)
        _, filename = tempfile.mkstemp()
        some_df.to_csv(filename)
        bucket.upload_file(filename, s3_key)


def append_to_csv(other, bucket_name, s3_key, save_index=False):
    """
    download the csv associated with bucket/s3_key (or create an empty one if bucket/s3_key is empty)
    add the contents of row and save it back into bucket/s3_key  
    :param other: 
    :param bucket: 
    :param s3_key: 
    :return: 
    """
    _, temp = tempfile.mkstemp()
    bucket = config.s3_client.Bucket(bucket_name)

    object = bucket.Object(s3_key)
    try:
        object.download_file(temp)
        if save_index:
            df = pd.read_csv(temp, index_col=0, comment='#')
        else:
            df = pd.read_csv(temp, comment='#')
    except:
        df = pd.DataFrame([])

    if type(other) == pd.Series:
        other = other.to_frame().T

    df = df.append(other)
    if os.environ['PORTFOLIO_REPORT']:
        df.to_csv(temp, index=save_index)
        bucket.upload_file(temp, s3_key)
    return df


def put_csv(df, bucket_name, s3_key, **kwargs):
    """
    Put dataframe from csv into bucketname and s3_key
    :param bucket_name: 
    :param s3_key: 
    :return: 
    """
    bucket = config.s3_client.Bucket(bucket_name)

    _, temp = tempfile.mkstemp()
    df.to_csv(temp, **kwargs)
    bucket.upload_file(temp, s3_key)


def get_df(bucket_name, s3_key, **read_csv_kwarg):
    """
    Get dataframe from csv associated with bucketname and s3_key and return it
    If any problem returns an empty DF
    :param bucket_name: 
    :param s3_key: 
    :return: 
    """
    bucket = config.s3_client.Bucket(bucket_name)

    object = bucket.Object(s3_key)
    _, temp = tempfile.mkstemp()
    try:
        object.download_file(temp)
        read_csv_kwarg.update({'comment': '#'})
        df = pd.read_csv(temp, **read_csv_kwarg)
    except:
        df = pd.DataFrame([])

    return df


def bucket_timestamps(bucket_name):
    """
    
    :param bucket_name: 
    :return: 
    return all timestamps in the given bucket/<account>/<time_stamp>_suffix

    """
    bucket = config.s3_client.Bucket(bucket_name)
    all_summaries = bucket.objects.all()
    s3_keys = [summary.key for summary in all_summaries]

    # limit s3_keys to current account and those with digits on them
    s3_keys = [key for key in s3_keys if os.environ['BITTREX_ACCOUNT'] in key]
    print s3_keys
    regex = re.compile('.*\d+')
    s3_keys = [key for key in s3_keys if regex.match(key)]
    print s3_keys

    regex = re.compile('\d+')
    times = [int(regex.findall(s3_key)[0]) for s3_key in s3_keys]
    return times

