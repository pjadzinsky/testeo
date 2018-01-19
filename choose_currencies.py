#!/usr/bin/python
"""
Do some analysis based on volume, volatility, trends, sentiment analysis and choose best currencies to hold

"""
import os
import time
import tempfile

import pandas as pd

import config

ONEDAY = 86400
NDAYS = 14
MIN_VOLUME = 1E6


def main():
    t1 = time.time()
    # Download all the markets during the last 2 weeks
    volumes_df = get_volumes()
    volumes_series = volumes_df.mean(axis=1)
    volumes_series.sort_values(ascending=False, inplace=True)

    variance_df = get_hourly_markets()
    variance_series = variance_df.std() / variance_df.mean()
    # variance_series is indexed by currency-pairs. I don't care what the base currency is, remove it from the index
    # but we could end up with two rows with the same index !!!
    # each index is of the form 'XXX-YYY' and we want just 'YYY'
    new_index = [s.split('-')[1] for s in variance_series.index.tolist()]
    variance_series.index = new_index

    # pick only curencies of volumes_series above MIN_VOLUME
    currencies = volumes_series[volumes_series > MIN_VOLUME].index.tolist()

    top = variance_series[currencies]
    top.sort_values(ascending=False, inplace=True)

    print top
    print time.time() - t1


def get_hourly_markets():
    bucket = config.s3_client.Bucket(config.MARKETS_BUCKET)
    objects_iterator = bucket.objects.filter(Prefix=os.environ['EXCHANGE'])

    _, temp = tempfile.mkstemp(suffix='.json')
    now = time.time()

    df = pd.DataFrame([])
    for object in objects_iterator:
        timestamp = None
        try:
            timestamp = int(object.key.split('/')[-1])
        except ValueError:
            pass
        except:
            raise

        if timestamp > now - NDAYS * ONEDAY:
            bucket.download_file(object.key, temp)

            temp_df = pd.read_json(temp)['Last']
            df = df.append(temp_df, ignore_index=True)

    return df


def get_volumes():
    bucket = config.s3_client.Bucket(config.MARKETS_BUCKET)
    s3_key = '{exchange}/markets_volumes.csv'.format(exchange=os.environ['EXCHANGE'])
    print s3_key
    print 'BITTREX/markets_volumes.csv'
    _, temp = tempfile.mkstemp(suffix='.csv')
    bucket.download_file(s3_key, temp)

    df = pd.read_csv(temp, header=0, index_col=0)

    now = time.time()
    columns_to_keep = [c for c in df.columns if int(c) > now - NDAYS * ONEDAY]
    df = df[columns_to_keep]
    return df

if __name__ == "__main__":
    main()
