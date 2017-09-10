#!/usr/bin/python
import os
import sys
from collections import namedtuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from market import market
from portfolio import portfolio
import bittrex_utils


ONEDAY = 86400.0
Result = namedtuple('Results', ['currencies', 'hour', 'rebalance', 'times', 'values', 'percentage_to_baseline',
                                'rate'])


def simulate_set(state, hours, markets, min_percentage_change, base, value):
    """ Just run 'simulate' for each hour in 'hours' and append the results
    All other parameters are the same except that the 1st hour is simulated
    twice, first with 'rebalance' set to False as the baseline
    """
    # compute the baseline
    baseline = simulate(state, min(hours), markets, min_percentage_change, False, base, value)
    baseline_rate = compute_rate(baseline)
    save_result(state, min(hours), False, baseline, baseline_rate, 0)

    for hour in hours:
        data = simulate(state, hour, markets, min_percentage_change, True, base, value)

        percentage_to_baseline = compute_percentage_from_baseline(baseline, data)
        data_rate = compute_rate(data)
        save_result(state, hour, True, data, data_rate, percentage_to_baseline)


def save_result(state, hour, rebalance, data, data_rate, percentage_to_baseline):
    currencies = portfolio.currencies_from_state(state)
    N = len(currencies)
    datadict = {'N':N,
                'rebalance': rebalance,
                'hour': hour,
                'time': [data['time'].tolist()],
                'value': [data['value'].tolist()],
                'rate': data_rate,
                'percentage_to_baseline': percentage_to_baseline}

    # first add all currencies to the dict as key with associated value of 'False'
    datadict.update({currency: False for currency in bittrex_utils.currencies_df().index})

    # Now change the value to True for those currencies used in the simulation
    datadict.update({currency: True for currency in currencies})

    # generate the DataFrame
    df = pd.DataFrame(datadict)

    fname = '/var/tmp/temp.csv'
    if not os.path.isfile(fname):
        df.to_csv(fname)
    else:
        with open(fname, 'a') as fid:
            df.to_csv(fid, header=False)


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
    return data


def compute_percentage_from_baseline(baseline, data):
    """ Compute percentage of increase last 'result' value has when compared to 'baseline' at the same time
    """
    last_result_time = data.time.values[-1]
    last_result_value = data.value.values[-1]
    baseline_at_time = baseline.value[baseline.time.values.searchsorted(last_result_time)]

    return (last_result_value - baseline_at_time) / baseline_at_time


def compute_rate(data):
    days = data['time'].iloc[-1] - 1
    last_value = data['value'].iloc[-1]
    first_value = data['value'].iloc[0]

    # rate ** days = last_value / first_value
    # days * log(base) = log(last_value / first_value)
    # base = 10**(log(last_value / first_value) / days)
    rate = 10 ** (np.log10(last_value/first_value) / days)

    return rate


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


