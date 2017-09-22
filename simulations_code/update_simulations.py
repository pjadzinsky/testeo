#!/usr/bin/python
import os
import sys

import gflags

from market import market
from simulations_code import simulate

FLAGS = gflags.FLAGS


def main():
    params_df = simulate.params_df

    markets = market.Markets(3600, 0)
    import pudb
    pudb.set_trace()
    for index, row in params_df.iterrows():
        markets.reset()
        simulate.simulate(markets, row)

if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    main()
