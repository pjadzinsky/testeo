#!/usr/bin/python
import sys

import gflags

from portfolio import portfolio
from simulations_code import simulate
import market

gflags.DEFINE_multi_int('hours', [1, 2, 3, 6, 12, 24], 'Hours in between market')
gflags.DEFINE_float('min_percentage_change', 0.1, "Minimum variation in 'balance' needed to place an order."
                    "1 is 100%")
gflags.DEFINE_integer('N', None, "Number of currencies to use")
gflags.DEFINE_boolean('random', None, "Whether to use 'N' random currencies from the given list")
gflags.DEFINE_string('currencies', None, "comma separated list of currencies")
FLAGS = gflags.FLAGS
gflags.RegisterValidator('min_percentage_change', lambda x: x >=0, 'Should be positive or 0')


BASE = 'USDT'
VALUE = 10000


if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print("%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS))
        sys.exit(1)

    #np.random.seed(1)
    # do only one data without rebalancing as a baseline
    hour = min(FLAGS.hours)
    markets = market.Markets(3600 * hour, 0)

    if FLAGS.currencies:
        currencies = FLAGS.currencies.split(',')
        currencies.sort()

    if FLAGS.N and FLAGS.random and FLAGS.currencies:
        desired_state = portfolio.random_state(currencies, FLAGS.N)
    elif FLAGS.currencies:
        desired_state = portfolio.state_from_currencies(currencies)
    elif FLAGS.N:
        desired_state = portfolio.state_from_largest_markes(markets.first_market(), FLAGS.N)

    print("Deisred State is:")
    print(desired_state)
    simulate.simulate_set(desired_state, BASE, VALUE, FLAGS.hours, markets, FLAGS.min_percentage_change)
