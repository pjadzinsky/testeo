#!/usr/bin/python
import sys

import gflags

from market import market

gflags.DEFINE_bool('ascending', False, '')
FLAGS = gflags.FLAGS


def main():
    markets = market.Markets(3600, 0)

    """
    volumes_df = markets.stats_volume()
    print '*' * 80
    print 'market volumes'
    print volumes_df.head(20)
    """

    #first = markets.last_market()
    #print first.inconsistencies()
    #s = first.last_in_usdt(['BTC'])
    #s.sort_values(inplace=True, ascending=False)
    #print s


    variance_df = markets.stats_variance(12)
    print variance_df.mean(axis=0)

    print ''
    print '*' * 80
    #print variance_df.head(20)

if __name__ == "__main__":
    FLAGS(sys.argv)

    main()
