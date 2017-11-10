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

    print '*' * 80
    print 'FLAGS.simulating:', FLAGS.simulating
    # currently we have only XRP in bittrex, start a portfolio with 'desired' state given only by 'XRP' and 'ETH'
    desired_state = portfolio.state_from_currencies(['ADA', 'TRIG', 'OK', 'RISE', 'IOP', 'NAV', 'MONA', 'EMC2',
                                                     'ADX', 'VTC', 'MCO', 'XVG', 'SYS', 'XLM', 'KMD', 'TKN'])

    current_market = market.Market.from_bittrex()
    #timestamp = 10
    #filename = os.path.expanduser('~/Testeo/simulations_data/markets/1502981286_short')
    #current_market = market.Market.from_local_file(filename, timestamp)
    p = portfolio.Portfolio.from_bittrex()

    # The first time, I run with this series, limit = pd.Series({'XRP': 0, 'ETH': 0, 'BTC': 0.165})
    # but after the original portfolio was created I changed it to the next line, not spending more bitcoins but
    # just trading between selected cryptocurrencies
    # There is a problem with my implementation. When trades are not places, and BTC are not operated
    # some money might be shifting into BTC indefinitely.
    # When I started Portfolio_1, I originaly had 0.66038387 BTC
    # From those, I traded 0.165 BTC leaving a balance of 0.49538387 BTC
    # Therefore I have to trade anythhing over the balance 0.49538387 BTC
    btc_balance_to_trade = p.dataframe.loc['BTC', 'Available'] - 0.33038387
    limit = pd.Series({'XRP': 0, 'ETH': 0, 'BTC': btc_balance_to_trade})
    p.limit_to(limit)
    # log the current state
    s3_key = '{time}_portfolio.csv'.format(time=current_market.time)
    if FLAGS.for_real:
        portfolio.log_state(s3_key, p.dataframe)
    p.rebalance(current_market, desired_state, ['BTC'], 0, by_currency=False)
    print p.dataframe
    p.report_value(current_market, os.path.expanduser('~/Testeo/results/Portfolio_1/trading.csv'))

    print 'Current value is: {}(USD)'.format(p.total_value(current_market, ['USDT', 'BTC']))
    p2 = portfolio.Portfolio.from_csv(os.path.expanduser('~/Testeo/results/Portfolio_1/original_portfolio.csv'))
    p2.report_value(current_market, os.path.expanduser('~/Testeo/results/Portfolio_1/holding.csv'))

    p3 = portfolio.Portfolio.from_csv(os.path.expanduser('~/Testeo/results/Portfolio_1/original_bitcoins.csv'))
    p3.report_value(current_market, os.path.expanduser('~/Testeo/results/Portfolio_1/bitcoins.csv'))

