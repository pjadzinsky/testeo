#!/usr/bin/python
import os
import sys

import gflags

import bittrex_utils
from market import market
from portfolio import portfolio
import state
import report

gflags.DEFINE_float('min_percentage_change', 0.1, "Minimum variation in 'balance' needed to place an order."
                    "1 is 100%")
gflags.DEFINE_string('state_csv', None, "path to csv containing a 'state'")

FLAGS = gflags.FLAGS
gflags.RegisterValidator('min_percentage_change', lambda x: x >= 0, 'Should be positive or 0')


def main(json_input, context):
    print '*' * 80
    print 'cancel all open orders'
    bittrex_utils.cancel_all_orders()

    print '*' * 80
    print 'PORTFOLIO_SIMULATING:', os.environ['PORTFOLIO_SIMULATING']
    print 'PORTFOLIO_FOR_REAL:', os.environ['PORTFOLIO_FOR_REAL']
    # currently we have only XRP in bittrex, start a portfolio with 'desired' state given only by 'XRP' and 'ETH'
    currencies = os.environ['CURRENCIES'].split(',')
    desired_state = state.from_currencies(currencies)
    print '*'*80
    print 'Desired state:'
    print desired_state

    current_market = market.Market.from_bittrex()
    p = portfolio.Portfolio.from_bittrex()
    print 'Current Portfolio'
    print p.dataframe

    # log the current state
    if os.environ['PORTFOLIO_FOR_REAL']:
        p.to_s3()
    msg = p.rebalance(current_market, desired_state, ['BTC'], 0, by_currency=False)
    print msg

    state.update_state(current_market.time, desired_state)
    report.report()


if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    main(None, None)
