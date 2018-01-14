import json
import os
import tempfile
import re

import pandas as pd

import config
print 'Finished with imports in', __file__


def log_df(bucket_name, s3_key, some_df):
    if os.environ['PORTFOLIO_REPORT'] == 'True':
        bucket = config.s3_client.Bucket(bucket_name)
        _, filename = tempfile.mkstemp()
        some_df.to_csv(filename)
        bucket.upload_file(filename, s3_key)


def append_to_csv(other, bucket_name, s3_key, **kwargs):
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
        df = pd.read_csv(temp, comment='#')
    except:
        df = pd.DataFrame([])
        kwargs.update({'index': True})

    if type(other) == pd.Series:
        other = other.to_frame().T

    df = df.append(other)
    if os.environ['PORTFOLIO_REPORT'] == 'True':
        df.to_csv(temp, **kwargs)
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
    all_summaries = bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])
    s3_keys = [summary.key for summary in all_summaries]

    regex = re.compile('.*\d+')
    s3_keys = [key for key in s3_keys if regex.match(key)]

    regex = re.compile('\d+')
    times = [int(regex.findall(s3_key)[0]) for s3_key in s3_keys]
    return times


def upload_json(data, bucket_name, s3_key):
    bucket = config.s3_client.Bucket(bucket_name)

    _, temp = tempfile.mkstemp()
    with open(temp, 'w') as fid:
        json.dump(data, fid)

    bucket.upload_file(temp, s3_key)


def download_json(bucket_name, s3_key):
    bucket = config.s3_client.Bucket(bucket_name)

    object = bucket.Object(s3_key)
    _, temp = tempfile.mkstemp()
    object.download_file(temp)
    with open(temp, 'r') as fid:
        data = json.load(fid)
    return data

