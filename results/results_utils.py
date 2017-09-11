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
FOLDER = os.path.expanduser('~/Testeo/simulation/')
FNAME = os.path.join(FOLDER, 'results.csv')

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

    if not os.path.isfile(FNAME):
        df.to_csv(FNAME, index=False)
    else:
        with open(FNAME, 'a') as fid:
            df.to_csv(fid, index=False, header=False)


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
    """ Compute interest rate yielded by data
    """
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


def plot_result():
    import holoviews as hv
    hv.extension('bokeh')
    renderer = hv.Store.renderers['bokeh'].instance(fig='html')

    df = pd.read_csv(FNAME)

    holoMap = hv.HoloMap({N:hv.Scatter(df[df['N']==N], kdims=['rate'], vdims=['percentage_to_baseline']) for N in
                          [4, 8, 16]}, kdims=['N'])
    holoview = holoMap.select(N={4, 8, 16}).layout()
    renderer.save(holoview, os.path.join(FOLDER, 'layout_II'), sytle=dict(Image={'cmap':'jet'}))


def evaluate_hour():
    """
    For each simulation set (the only thing that changes is time). Sort hours by some type of return. Then compute
    the mean and std of the ordering of a given hour. Is 1hour the best?
    
    :return: 
    """
    df = pd.read_csv(FNAME)

    # to identify a simulation we can just look at rows with 'rebalanced' set to False

    baselines = df[df['rebalance']==False]
    baselines_index = baselines.index.tolist()

    # add to 'baselines_index' the index corresponding to the next empty row so that extracting all data for a
    # simulation is just extracting between baselines_index[i] and baselines_index[i+1]
    baselines_index.append(df.shape[0])

    output_df = pd.DataFrame([])

    for start, end in zip(baselines_index[:-1], baselines_index[1:]):
        temp = df.iloc[start:end]
        sim_name = csv_row_to_name(temp.iloc[0])
        sorted_order = np.argsort(temp['percentage_to_baseline'].values)
        hours = temp['hour'].values
        s = pd.Series(sorted_order, index=hours, name=sim_name)
        output_df = pd.concat([output_df, s], axis=1)

    mean = output_df.mean(axis=1)
    std = output_df.std(axis=1)
    return mean, std

def csv_row_to_name(row):
    """
    return a friendly name from a csv row
    """
    # keep only boolean values
    boolean_row = row.select(lambda i: type(row[i])==np.bool_ and row[i])
    if 'rebalance' in boolean_row.index:
        boolean_row.drop('rebalance', inplace=True)

    return '_'.join([str(i) for i in boolean_row.index])
"""
Analysis for /var/tmp/temp.csv

1) For each simulation set (the only thing that changes is time). Sort hours by some type of return. Then make the mean
and std of the ordering index. Is 1hour the best?

2) For each simulation condition (N, hour) compute the mean and std. Color plot or similar where the two dimensions are
N and hour?

3) Just plot in a 2D plot as in 2 all the results
"""
