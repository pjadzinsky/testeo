#!/usr/bin/python
import sys

import gflags

from markets import recreate_markets
from portfolio import portfolio

gflags.DEFINE_integer('delay', 1, 'Hours in between markets')
gflags.DEFINE_float('min_percentage_change', 0.1, "Minimum variation in 'balance' needed to place an order."
                    "Should be between 0 and 1")
FLAGS = gflags.FLAGS
gflags.RegisterValidator('min_percentage_change', lambda x: x >=0, 'Should be positive or 0')


def simulation(delay, min_percentage_change):
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'

    all_markets = recreate_markets.get_markets()
    market_times = all_markets.index.levels[0].tolist()
    market_times.sort()
    market_time = market_times[0]

    first_market = recreate_markets.first_market()
    N = 20
    base = 'USDT'
    value = 10000
    state = portfolio.uniform_state(first_market, N, include_usd=False)
    position = portfolio.start_portfolio(first_market, state, base, value)


    while True:
        market = recreate_markets.closest_market(market_time)
        position.rebalance(market, state, ['BTC', 'USDT'], min_percentage_change)
        print market_time, value, min_percentage_change, position.total_value(market, ['BTC', 'USDT'])
        market_time += delay * 3600
        if market_time > market_times[-1]:
            break

    """
    base_currency = 'USDT'
    value = 10000

    if portfolio is None:
        portfolio = volume.Portfolio()
        portfolio.start_portfolio(market, state, 'USDT', value)
        header = True
    else:
        header = False

    portfolio.ideal_rebalance(market, state)

    market.to_csv(header=header)
    portfolio.to_csv()

    print "Market value:", portfolio.total_value(market, ['BTC', 'USDT'])
    """

    #

    """
    value = 10

    market = volume.Market()
    state = volume.define_state(market, 20, include_usd=True)
    base_currency = 'BTC'
    value = 10000

    portfolio = volume.Portfolio.from_csv()
    if portfolio is None:
        portfolio = volume.Portfolio()
        portfolio.start_portfolio(market, state, 'USDT', value)
        header = True
    else:
        header = False

    portfolio.ideal_rebalance(market, state)

    market.to_csv(header=header)
    portfolio.to_csv()

    print "Market value:", portfolio.total_value(market, ['BTC', 'USDT'])
    """


if __name__ == "__main__":
    gflags.FLAGS(sys.argv)
    simulation(FLAGS.delay, FLAGS.min_percentage_change)
