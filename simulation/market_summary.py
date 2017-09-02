#!/usr/bin/python
import sys

import gflags

from market import market

gflags.DEFINE_bool('ascending', False, '')
FLAGS = gflags.FLAGS


def main():
    markets = market.Markets(830600, 0)
    """
    volumes_df = markets.volume()
    print '*' * 80
    print 'market volumes'
    print volumes_df
    print ''
    """
    variance_df, volume_df = markets.stats()
    print '*' * 80
    print variance_df, volume_df

if __name__ == "__main__":
    FLAGS(sys.argv)

    main()
