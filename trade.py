#!/usr/bin/python
import os
import json
import sys

import gflags
import pandas as pd

from market import market
from portfolio import portfolio

gflags.DEFINE_float('min_percentage_change', 0.1, "Minimum variation in 'balance' needed to place an order."
                    "1 is 100%")
gflags.DEFINE_string('state_csv', None, "path to csv containing a 'state'")

FLAGS = gflags.FLAGS
gflags.RegisterValidator('min_percentage_change', lambda x: x >= 0, 'Should be positive or 0')


def main(json_input, context):
    print '*' * 80
    print 'PORTFOLIO_SIMULATING:', os.environ['PORTFOLIO_SIMULATING']
    print 'PORTFOLIO_FOR_REAL:', os.environ['PORTFOLIO_FOR_REAL']
    # currently we have only XRP in bittrex, start a portfolio with 'desired' state given only by 'XRP' and 'ETH'
    currencies = os.environ['CURRENCIES'].split(',')
    desired_state = portfolio.state_from_currencies(currencies)
    print '*'*80
    print desired_state

    current_market = market.Market.from_bittrex()
    p = portfolio.Portfolio.from_bittrex()

    # log the current state
    s3_key = '{time}_portfolio.csv'.format(time=current_market.time)
    if os.environ['PORTFOLIO_FOR_REAL']:
        portfolio.log_state(s3_key, p.dataframe)
    msg = p.rebalance(current_market, desired_state, ['BTC'], 0, by_currency=False)
    print msg
    print 6
    print p.dataframe
    """
    p.report_value(current_market, os.path.expanduser('~/Testeo/results/Portfolio_1/trading.csv'))

    print 'Current value is: {}(USD)'.format(p.total_value(current_market, ['USDT', 'BTC']))
    p2 = portfolio.Portfolio.from_csv(os.path.expanduser(('~/Testeo/results/Portfolio_1/original_portfolio.csv')))
    p2.report_value(current_market, os.path.expanduser('~/Testeo/results/Portfolio_1/holding.csv'))

    return msg
    """


if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    main()
