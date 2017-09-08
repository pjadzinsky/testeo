#!/usr/bin/python
import sys

import gflags
import pandas as pd

from market import market

gflags.DEFINE_bool('ascending', False, '')
FLAGS = gflags.FLAGS


def main():
    markets = market.Markets(3600*24, 0)

    volumes = markets.stats_volume()
    print '*' * 80
    print 'market volumes'
    print volumes.head(20)

    #first = markets.last_market()
    #print first.inconsistencies()
    #s = first.last_in_usdt(['BTC'])
    #s.sort_values(inplace=True, ascending=False)
    #print s


    variance_df = markets.stats_variance(12)
    mean_variance = variance_df.mean(axis=0)

    mean_variance.sort_values(ascending=False, inplace=True)
    print mean_variance.head(20)
    print mean_variance.index.values[:30]
    print '*' * 80

    print type(volumes), type(mean_variance)
    df = pd.concat([volumes, mean_variance], axis=1)
    df.columns = ['volume', 'variance']
    df = df[df['volume'] > 1E6]
    df = df.sort_values('variance', ascending=False)
    print ','.join(df.index.values[:20])
    df.to_csv('/tmp/mean_variance.csv')


if __name__ == "__main__":
    FLAGS(sys.argv)

    main()
