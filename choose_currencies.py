#!/usr/bin/python
"""
Do some analysis based on volume, volatility, trends, sentiment analysis and choose best currencies to hold

This scritp requires env variables
    LOGNAME:    aws or pablo, in aws we use default profile, in my laptop I use a different one
    EXCHANGE: POLONIEX or BITTREX for the time being
    EXCHANGE_ACCOUNT:   String to identify account within an exchange. Only used in logging and grabing data from s3
                        has nothing to do with operating since that is determined by the <EXCHANGE>_KEY/SECRET
"""
import os
import time
import tempfile

import pandas as pd

import config
import s3_utils

ONEDAY = 86400
NDAYS = 14
MIN_VOLUME = 1E6
N = 10


def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


def main():
    now = int(time.time())

    # Download all the markets during the last NDAYS defined above.
    volumes_df = get_volumes()
    # compute mean per currency and sort from higest to lowest
    volumes_series = volumes_df.mean(axis=1)
    volumes_series.sort_values(ascending=False, inplace=True)

    # Get hourly markets over the last NDAYS
    variance_df = get_hourly_markets()
    # compute the contrast
    variance_series = variance_df.std() / variance_df.mean()
    # variance_series is indexed by currency-pairs. I don't care what the base currency is, remove it from the index
    # but we could end up with two rows with the same index !!!
    # each index is of the form 'XXX-YYY' and we want just 'YYY'
    new_index = [s.split('-')[1] for s in variance_series.index.tolist()]
    variance_series.index = new_index

    # pick only curencies of volumes_series above MIN_VOLUME
    currencies = volumes_series[volumes_series > MIN_VOLUME].index.tolist()

    # keep variances of only the those currencies wtih volumes above MIN_VOLUME
    top = variance_series[currencies]

    # compute the mean over the index. As explained above, since variance_series is originaly over currency-pairs,
    # if we have items in the index like XXX-ZZZ and YYY-ZZZ they both map to 'new_index' ZZZ. Here we are averaging
    # over them
    top = top.groupby(by=lambda x: x).mean()
    top.sort_values(ascending=False, inplace=True)

    upload_series(top, now)

    upload_currencies(top.index[:N], now)


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
    _, temp = tempfile.mkstemp(suffix='.csv')
    bucket.download_file(s3_key, temp)

    df = pd.read_csv(temp, header=0, index_col=0)

    now = time.time()
    columns_to_keep = [c for c in df.columns if int(c) > now - NDAYS * ONEDAY]
    df = df[columns_to_keep]
    return df


def upload_series(top, time):
    bucket = s3_utils.get_write_bucket(config.CURRENCIES_BUCKET)

    _, temp = tempfile.mkstemp(suffix='.csv')
    print temp

    s3_key = '{exchange}/{account}/{time}.csv'.format(
        exchange=os.environ['EXCHANGE'],
        account=os.environ['EXCHANGE_ACCOUNT'],
        time=time)

    top.to_csv(temp)
    bucket.upload_file(temp, s3_key)

    print 'uploaded {} to {}'.format(s3_key, bucket.name)


def upload_currencies(currencies, time):
    bucket = s3_utils.get_write_bucket(config.CURRENCIES_BUCKET)

    s3_key = '{exchange}/{account}/currencies.csv'.format(
        exchange = os.environ['EXCHANGE'],
        account = os.environ['EXCHANGE_ACCOUNT']
    )

    try:
        _, temp = tempfile.mkstemp(suffix='.csv')
        bucket.download_file(s3_key, temp)
        df = pd.read_csv(temp, index_col=0)
        df.columns = [int(c) for c in df.columns]
    except:
        df = pd.DataFrame([])

    s = pd.Series(currencies)
    s.name = time
    df = df.append(s)

    df.to_csv(temp)
    bucket.upload_file(temp, s3_key)
    print 'updated {} to {}'.format(s3_key, bucket.name)


if __name__ == "__main__":
    main()
