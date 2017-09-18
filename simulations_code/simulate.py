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


ONEHOUR = 3600
ONEDAY = 86400.0
FOLDER = os.path.expanduser('~/Testeo/simulations_data/')
PARAMS = os.path.join(FOLDER, 'params.csv')
DATAFOLDER = os.path.join(FOLDER, 'data')
PARAMS_INDEX_THAT_ARE_NOT_CURRENCIES = ['N', 'time', 'value', 'timestamp', 'hour', 'min_percentage_change',
                                        'is_baseline']

try:
    os.makedirs(DATAFOLDER)
except:
    pass

try:
    params_df = pd.read_csv(PARAMS, index_col=0)
except:
    params_df = pd.DataFrame([])
    params_df.index.name = 'index'


def simulate_set(initial_portfolio, desired_state, hours, markets, min_percentage_change):
    """ Just run 'simulate' for each hour in 'hours' and append the simulations_code
    All other parameters are the same except that the 1st hour is simulated
    twice, first with 'is_baseline' set to True as the baseline
    """
    timestamp = int(time.time())
    # compute the baseline
    params_dict = {'hour': min(hours), 'is_baseline': True, 'min_percentage_change': min_percentage_change}
    simulation_index = save_simulaton_params(timestamp, desired_state, params_dict)
    print 'Simulation Index: ', simulation_index
    simulate(simulation_index, initial_portfolio.copy(), desired_state, markets, params_dict)

    params_dict['is_baseline'] = False
    import pudb
    pudb.set_trace()
    for hour in hours:
        markets.reset(seconds=ONEHOUR * hour)
        params_dict['hour'] = hour
        simulation_index = save_simulaton_params(timestamp, desired_state, params_dict)
        print 'Simulation Index: ', simulation_index
        simulate(simulation_index, initial_portfolio.copy(), desired_state, markets, params_dict)


def update_simulations(markets, min_percentage_change):
    """
    What is this????
    :param markets: 
    :param min_percentage_change: 
    :return: 
    """
    for index in params_df.index:
        # needs access to the desired desired_state
        desired_state = state_from_params(index)
        hour = params_df.loc[index, 'hour']
        is_baseline = params_df.loc[index, 'is_baseline']
        simulate(index, desired_state, hour, markets, min_percentage_change, is_baseline)


def index_from_params(desired_state, params_dict):
    """ Return index corresponding to the parameters
    
    A new row will be added to the PARAMS csv if no matches are found.
    """
    target_row = series_from_parameters(desired_state, params_dict)
    for index, row in params_df.iterrows():
        if np.all(row.drop('timestamp') == target_row):
            return index

    return None


def save_simulaton_params(timestamp, desired_state, params_dict):
    """
    Add a row to PARAMS csv with the parameters from this simulation:
    
    New row has columns 'hour', 'is_baseline', 'min_percentage_change', 'timestamp' and one boolean column for each
    possible currency
    
    :param desired_state: 
    :param hour: 
    :param is_baseline: 
    :return: 
    """
    global params_df

    index = index_from_params(desired_state, params_dict)
    if index is None:
        # add data to PARAMS csv

        s = series_from_parameters(desired_state, params_dict)
        s['timestamp'] = timestamp


        params_df = params_df.append(s, ignore_index=True)
        params_df.to_csv(PARAMS)
        index = params_df.index[-1]
    return index


def simulate(sim_index, original_portfolio, desired_state, markets, params_dict):
    """
    
    :param sim_index: 
    :param desired_state: 
    :param markets: 
    :param base: 
    :param value: 
    :return: 
    """
    assert 'hour' in params_dict
    assert 'is_baseline' in params_dict
    assert 'min_percentage_change' in params_dict
    csv_filename = os.path.join(DATAFOLDER, '{0}.csv'.format(sim_index))
    if os.path.isfile(csv_filename):
        print 'csv found:', csv_filename
        data = pd.read_csv(csv_filename)
    else:
        data = pd.DataFrame([], columns=['time'])  # other columns will be added but right now we just need 'time'

    write_file = False
    for market in markets:
        if market.time in data['time'].values:
            # update original_portfolio
            original_portfolio.dataframe = portfolio_from_simulation(sim_index, market.time)
        else:
            write_file = True
            data = simulate_step(original_portfolio, desired_state, market, data, params_dict)

    if write_file:
        print "Saving {0}".format(csv_filename)
        data.to_csv(csv_filename, index=False)


def portfolio_from_simulation(sim_index, time):
    """
    Load the current portoflio for the given parameters
    
    :param sim_index: 
    :param time: 
    :return: 
    """
    csv_filename = os.path.join(DATAFOLDER, "{sim_index}.csv".format(sim_index=sim_index))
    data = pd.read_csv(csv_filename)
    row = data[data['time']==time]
    dataframe = row.drop(['time', 'value'], axis=1).T

    dataframe.columns = ['Balance']
    dataframe.loc[:, 'Available'] = dataframe['Balance']
    dataframe.loc[:, 'Pending'] = 0

    return dataframe

def simulate_step(current_portfolio, desired_state, market, data, params_dict):
    """ Do one stop of the simulation for the given parameters
    
    Writes files:
    DATAFOLDER/<sim_index>.csv with 'time', 'value', <currency1>, <currency2>, ..., <currencyN> columns
    """
    # try to load dataframe from DATAFOLDER/<index>.csv,
    # TODO this should move outside this function
    """

    markets.reset(seconds=3600 * hour)
    if current_time in data['time']:
        # don't simulate this step, we already have and the result is in the row with 'time' = current_time
        p.dataframe['Balance'] = data[data['time']==current_time].drop('time', 'value')
    data.to_csv(csv_filename, index=False)
    """

    time = market.time
    min_percentage_change = params_dict['min_percentage_change']
    is_baseline = params_dict['is_baseline']
    # we need to compute this step of simulation
    if is_baseline:
        pass
    else:
        current_portfolio.rebalance(market, desired_state, ['BTC'], min_percentage_change)

    value = current_portfolio.total_value(market, ['USDT', 'BTC'])
    s = current_portfolio.dataframe['Balance']
    s['time'] = time
    s['value'] = value

    data = data.append(s, ignore_index=True)
    return data


def state_from_params(sim_index):
    """ Generate a 'state' from all the currencies in the simulation
    
    We are getting the currencies from the params_df, where currencies happen in the index (there are other things in
    the index as well). To get the currencies in the simulation we first remove everything in the index that is not
    a currency and then keep only those currencies that are set (have value equal to True)
    """

    sim_params = params_df.loc[sim_index]
    currencies = [p for p in sim_params.index if sim_params[p] and p not in PARAMS_INDEX_THAT_ARE_NOT_CURRENCIES]

    return portfolio.state_from_currencies(currencies)



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

    # last 5 columns are: is_baseline, percentage_to_baseline, rate, time, value
    # and I want them to be:
    # mean %, rate, is_baseline, time, value
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
def series_from_parameters(desired_state, params_dict):
    # first add all currencies to the dict as key with associated value of 'False'
    datadict = {currency: False for currency in bittrex_utils.currencies_df().index}

    # Now change the value to True for those currencies used in the data
    currencies = portfolio.currencies_from_state(desired_state)
    datadict.update({currency: True for currency in currencies})

    datadict['N'] = len(currencies)
    datadict.update(params_dict)

    s = pd.Series(datadict)
    return s
