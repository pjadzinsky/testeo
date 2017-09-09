#!/usr/bin/python
import os
import sys
from collections import namedtuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from market import market
from portfolio import portfolio


ONEDAY = 86400.0
Result = namedtuple('Results', ['currencies', 'hour', 'rebalance', 'data'])


def simulate_set(state, hours, markets, min_percentage_change, base, value):
    """ Just run 'simulate' for each hour in 'hours' and append the results
    All other parameters are the same except that the 1st hour is simulated
    twice, first with 'rebalance' set to False as the baseline
    """
    results = []
    # compute the baseline
    results.append(simulate(state, min(hours), markets, min_percentage_change, False,
                            base, value))

    for hour in hours:
        results.append(simulate(state, hour, markets, min_percentage_change, True,
                                base, value))

    return results

def save_results(results):
    N = len(currencies)
    df = pd.DataFrame({'N': N, })
    fname = '/var/tmp/simulation.csv'
    if not os.path.isfile(fname):
        df.to_csv(fname)
    else:
        df.to_csv(fname)


def simulate(state, hour, markets, min_percentage_change, rebalance, base, value):
    times = []
    values = []
    markets.reset(seconds=3600 * hour)
    p = portfolio.Portfolio.from_state(markets.first_market(), state, base, value)
    for current_time, current_market in markets:
        times.append(current_time)
        if rebalance:
            p.rebalance(current_market, state, ['BTC'], min_percentage_change)

        values.append(p.total_value(current_market, ['USDT', 'BTC']))

    data = pd.DataFrame({'time': times, 'value': values})
    data['time'] = (data['time'] - data['time'].min()) / ONEDAY
    currencies = portfolio.currencies_from_state(state)
    return Result(currencies, hour, rebalance, data)


def last_baseline_difference(results):
    for r in results:
        if r.rebalance == False:
            last_baseline = r.data['value'].values[-1]

    for r in results:
        print r.hour, (r.data['value'].values[-1] - last_baseline) / last_baseline


def powers(results):
    # data with no rebalancing
    baseline = results[0].data
    base_times = baseline['time']
    base_values = baseline['value']

    output = {}
    for r in results[1:]:
        last_time = r.data['time'][-1]
        last_value = r.data['value'][-1]
        last_base_value = base_values[base_times.find(last_time)]
        days = (last_time - r.data['time'][0]) / 86400

        # base ** days = last_value / last_base_value
        # days * log(base) = log(last_value / last_base_value)
        # base = 10**gggg
        power = np.log(last_value/last_base_value) / np.log(days)

        output[r.hour] = power

    return output


def simulation_name(currencies, hours, min_percentage_change, suffix=None):
    """
    Return a string with all parameters used in the simulation
    
    :return: 
    """
    if currencies:
        name = "names_" + '_'.join(currencies) + \
               "_hours_" + "_".join([str(h) for h in hours]) + \
               "_%change_" + str(int(min_percentage_change * 100))
    if suffix:
        name += suffix

    return name


