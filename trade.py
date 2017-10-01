#!/usr/bin/python
import os
import sys

import gflags
import pandas as pd
import numpy as np

from market import market
from portfolio import portfolio
from simulations_code import simulate

gflags.DEFINE_multi_int('hour', 24, 'Hours in between market')
gflags.DEFINE_float('min_percentage_change', 0.1, "Minimum variation in 'balance' needed to place an order."
                    "1 is 100%")
gflags.DEFINE_string('state_csv', None, "path to csv containing a 'state'")
FLAGS = gflags.FLAGS
gflags.RegisterValidator('min_percentage_change', lambda x: x >= 0, 'Should be positive or 0')
#gflags.RegisterValidator('state_csv', os.path.isfile)


if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    # currently we have only XRP in bittrex, start a portfolio with 'desired' state given only by 'XRP' and 'ETH'
    desired_state = portfolio.state_from_currencies(['XRP', 'ETH'])

    current_market = market.Market.from_bittrex()
    #timestamp = 10
    #filename = os.path.expanduser('~/Testeo/simulations_data/markets/1502981286_short')
    #current_market = market.Market.from_local_file(filename, timestamp)
    p = portfolio.Portfolio.from_bittrex()
    print p.dataframe
    p.rebalance(current_market, desired_state, ['ETH'], 0, by_currency=False)
    print p.dataframe

