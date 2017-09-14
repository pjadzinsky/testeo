"""
This are helper functions in running a simulation. I'm still sorting it out.
Running a simulation is as of 09-14-2017 choosing currencies randomly and getting the markets and the results of
trading every so often to 'rebalance' the portfolio.
"""
import os
import json
import time
from itertools import product

import numpy as np
import pandas as pd

from portfolio import portfolio
import bittrex_utils


ONEDAY = 86400.0
FOLDER = os.path.expanduser('~/Testeo/simulations_data/test/')
PARAMS = os.path.join(FOLDER, 'params.csv')
DATAFOLDER = os.path.join(FOLDER, 'data')

try:
    os.makedirs(DATAFOLDER)
except:
    pass


def simulate_set(state, hours, markets, min_percentage_change, base, value):
    """ Just run 'simulate' for each hour in 'hours' and append the simulations_code
    All other parameters are the same except that the 1st hour is simulated
    twice, first with 'rebalance' set to False as the baseline
    """
    timestamp = int(time.time())
    # compute the baseline
    baseline = simulate(state, min(hours), markets, min_percentage_change, False, base, value)
    simulation_index = save_simulaton_params(timestamp, state, min(hours), False)
    save_data(simulation_index, baseline)

    for hour in hours:
        data = simulate(state, hour, markets, min_percentage_change, True, base, value)
        simulation_index = save_simulaton_params(timestamp, state, hour, True)
        save_data(simulation_index, data)


def save_simulaton_params(timestamp, state, hour, rebalance):
    """
    :param state: 
    :param hour: 
    :param rebalance: 
    :return: 
    """


    # first add all currencies to the dict as key with associated value of 'False'
    datadict = {currency: False for currency in bittrex_utils.currencies_df().index}

    # Now change the value to True for those currencies used in the data
    currencies = portfolio.currencies_from_state(state)
    datadict.update({currency: True for currency in currencies})

    datadict['timestamp'] = timestamp
    datadict['N'] = len(currencies)
    datadict['hour'] = hour
    datadict['rebalance'] = rebalance

    s = pd.Series(datadict)
    # load params.csv if it exists
    if os.path.isfile(PARAMS):
        params_df = pd.read_csv(PARAMS, index_col=0)
    else:
        params_df = pd.DataFrame([])
        params_df.index.name = 'index'

    params_df = params_df.append(s, ignore_index=True)
    params_df.to_csv(PARAMS)
    index_added = params_df.index[-1]
    return index_added


def save_data(simulation_index, data):
    data.to_csv(os.path.join(DATAFOLDER, '{0}.csv'.format(simulation_index)), index=False)


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


'''
def fix_csv():
    """
    Load the csv and fix it, modify as needed
    :return: 
    """
    df = pd.read_csv(PARAMS)

    df.drop(['rate', 'percentage_to_baseline'], axis=1, inplace=True)

    rates = []
    means = []

    for index, row in df.iterrows():
        temp_df = pd.DataFrame({'time': json.loads(row.time), 'value': json.loads(row.value)})
        compute_rate(temp_df)
        compute_mean_percentage(temp_df)
        rates.append([temp_df['rate'].tolist()])
        means.append([temp_df['mean %'].tolist()])
        #df.loc[index, 'rate'] = [temp_df['rate'].tolist()]
        #df.loc[index, 'mean %'] = [temp_df['mean %'].tolist()]

    df.loc[:, 'rate'] = rates
    df.loc[:, 'percentage_to_baseline'] = means
    columns = df.columns.tolist()

    # last 5 columns are: rebalance, percentage_to_baseline, rate, time, value
    # and I want them to be:
    # mean %, rate, rebalance, time, value
    # so the index order is: -4, -3, -5, -2, -1
    index = columns.index('percentage_to_baseline')
    columns[index] = 'mean %'
    df.columns = columns
    print columns[-5:]
    columns = columns[:-4] + [columns[-4], columns[-3], columns[-5]] + columns[-2:]
    print columns[-5:]
    df = df[columns]
    df.to_csv('test.csv', index=False)
'''
