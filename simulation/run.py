#!/usr/bin/python
import sys

import gflags

from markets import recreate_markets
from portfolio import portfolio

gflags.DEFINE_integer('delay', 1, 'Hours in between markets')
FLAGS = gflags.FLAGS


def simulation(delay):
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'

    all_markets = recreate_markets.get_markets()
    market_times = all_markets.index.levels[0]
    market_times = market_times[::delay]

    first_market = recreate_markets.first_market()
    N = 20
    base = 'USDT'
    value = 10000
    state = portfolio.uniform_state(first_market, N, include_usd=True)
    position = portfolio.start_portfolio(first_market, state, base, value)

    for i, market_time in enumerate(market_times):
        market = recreate_markets.market_at_time(market_time)
        position.rebalance(market, state, ['BTC', 'USDT'])
        print i, value, position.total_value(market, ['BTC', 'USDT'])
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
    simulation(FLAGS.delay)
