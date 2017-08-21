#!/usr/bin/python
import sys

import gflags
import pandas as pd

from markets import recreate_markets
from markets import market_operations
from portfolio import portfolio

gflags.DEFINE_bool('ascending', False, '')
FLAGS = gflags.FLAGS


def main():
    markets = recreate_markets.get_markets()
    mean_volumes_df = market_operations.volume(markets, ascending=FLAGS.ascending)
    print mean_volumes_df

if __name__ == "__main__":
    FLAGS(sys.argv)

    main()
