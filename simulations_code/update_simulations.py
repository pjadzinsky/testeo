#!/usr/bin/python
import sys

import gflags

from simulations_code import simulate
import market

FLAGS = gflags.FLAGS


def main():
    params_df = simulate.params_df

    markets = market.Markets(3600, 0)
    for index, row in params_df.iterrows():
        hour = row['hour']
        markets.reset(seconds=3600 * hour)
        simulate.simulate(markets, row)

if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    main()
