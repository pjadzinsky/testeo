import os
import tempfile

import pandas as pd

import config

def log_df(bucket_name, s3_key, some_df):
    bucket = config.s3_client.Bucket(bucket_name)
    _, filename = tempfile.mkstemp()
    some_df.to_csv(filename)
    bucket.upload_file(filename, s3_key)


def update_csv(other, bucket_name, s3_key_suffix):
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
    s3_key_suffix = s3_key_suffix.rstrip('.csv')    # just in case, ".csv" is added below again
    s3_key = '{account}/{suffix}.csv'.format(account=os.environ['BITTREX_ACCOUNT'],
                                             suffix=s3_key_suffix)
    object = bucket.Object(s3_key)
    try:
        object.download_file(temp)
        df = pd.read_csv(temp, comment='#')
    except:
        df = pd.DataFrame([])

    if type(other) == pd.Series:
        other = other.to_frame().T

    df = df.append(other)

    df.to_csv(temp, index=False)
    bucket.upload_file(temp, s3_key)


def get_df(bucket_name, s3_key_suffix):
    """
    Get dataframe from csv associated with bucketname and s3_key_suffix and return it
    If any problem returns an empty DF
    :param bucket_name: 
    :param s3_key_suffix: 
    :return: 
    """
    bucket = config.s3_client.Bucket(bucket_name)
    s3_key = "{account}/{s3_key_suffix}".format(account=os.environ['BITTREX_ACCOUNT'],
                                                s3_key_suffix=s3_key_suffix)

    object = bucket.Object(s3_key)
    _, temp = tempfile.mkstemp()
    try:
        object.download_file(temp)
        df = pd.read_csv(temp, comment='#')
    except:
        df = pd.DataFrame([])

    return df
