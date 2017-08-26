#!/usr/bin/python
import sys

import gflags
import pandas as pd
import matplotlib.pyplot as plt

from market import market
from portfolio import portfolio

gflags.DEFINE_multi_int('hours', [6, 12, 24, 36, 48], 'Hours in between market')
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

base = 'USDT'
value = 10000
to_usdt = ['BTC', 'USDT']

def compare_simulations(hours, min_percentage_change, N, currencies):
    fig, ax = plt.subplots()
    dfs = [baseline(12, N, currencies)]
    dfs[0].plot(x='time', y='value', ax=ax)

    for hour in hours:
        df = simulation(hour, min_percentage_change, N, currencies)
        dfs.append(df)
        df.plot(x='time', y='value', ax=ax)

    plt.show()
    print df


def first_position(N, currencies):
    first_market = market.first_market()

    if N:
        state = portfolio.uniform_state(first_market, N, include_usd=False)
    elif currencies:
        state = custom_state(currencies.split(','))

    position = portfolio.start_portfolio(first_market, state, base, value)

    return state, position


def baseline(hours, N, currencies):
    first_market = market.first_market()
    desired_state, position = first_position(N, currencies)
    position.rebalance(first_market, desired_state, to_usdt, 0)

    markets = market.Market
    return df


def simulation(markets, min_percentage_change, N, currencies):
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'
    if currencies:
        state, p = portfolio.Portfolio.from_currencies(markets.first_market(), currencies, base, value)
    elif N:
        state, p = portfolio.Portfolio.from_largest_markes(markets.first_market(), N, base, value)

    total_values = []
    times = []
    for time, current_market in markets:
        p.rebalance(current_market, state, ['BTC'], min_percentage_change)
        times.append(time)
        total_values.append(p.total_value(current_market, ['BTC']))

    df = pd.DataFrame({'time': times, 'value': total_values})
    return df


if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    markets = market.Markets(3600 * 24, 0)
    print simulation(markets, 0, FLAGS.N, FLAGS.currencies)
