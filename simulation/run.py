#!/usr/bin/python
import sys

import gflags
import pandas as pd
import matplotlib.pyplot as plt

from markets import recreate_markets
from portfolio import portfolio

gflags.DEFINE_multi_int('hours', [6, 12, 24, 36, 48], 'Hours in between markets')
gflags.DEFINE_float('min_percentage_change', 0.1, "Minimum variation in 'balance' needed to place an order."
                    "Should be between 0 and 1")
gflags.DEFINE_integer('N', None, "Number of currencies to use")
gflags.DEFINE_string('currencies', None, "comma separated list of currencies")
FLAGS = gflags.FLAGS
gflags.RegisterValidator('min_percentage_change', lambda x: x >=0, 'Should be positive or 0')

@gflags.multi_flags_validator(['N', 'currencies'], 'One has to be defined')
def _XOR(flags_dict):
    if not flags_dict['N'] and not flags_dict['currencies']:
        return False
    if flags_dict['N'] and flags_dict['currencies']:
        return False
    return True


def compare_simulations(hours, min_percentage_change, N, currencies):
    dfs = []
    fig, ax = plt.subplots()
    for hour in hours:
        df = simulation(hour, min_percentage_change, N, currencies)
        dfs.append(df)
        df.plot(x='time', y='value', ax=ax)

    plt.show()
    print df


def simulation(hours, min_percentage_change, N, currencies):
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'

    all_markets = recreate_markets.get_markets()
    market_times = all_markets.index.levels[0].tolist()
    market_times.sort()
    market_time = market_times[0]

    first_market = recreate_markets.first_market()
    base = 'USDT'
    value = 10000

    if N:
        state = portfolio.uniform_state(first_market, N, include_usd=False)
    elif currencies:
        state = custom_state(currencies.split(','))

    position = portfolio.start_portfolio(first_market, state, base, value)

    total_values = []
    times = []
    while True:
        market = recreate_markets.closest_market(market_time)
        position.rebalance(market, state, ['BTC', 'USDT'], min_percentage_change)
        times.append(market_time)
        total_values.append(position.total_value(market, ['BTC', 'USDT']))
        print market_time, position.total_value(market, ['BTC', 'USDT'])
        market_time += hours * 3600
        if market_time > market_times[-1]:
            break

    df = pd.DataFrame({'time': times, 'value': total_values})
    return df


def custom_state(currencies):
    """
    Define a custome state
    :return: 
    """
    N = len(currencies)
    state = pd.DataFrame({'Weight': [1.0/N] * N}, index=currencies)
    return state


if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    compare_simulations(FLAGS.hours, FLAGS.min_percentage_change, FLAGS.N, FLAGS.currencies)
