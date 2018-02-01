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

import config
from portfolio import portfolio
from exchanges import exchange


try:
    os.makedirs(config.DATAFOLDER)
except:
    pass

try:
    params_df = pd.read_csv(config.PARAMS, index_col=0)
except:
    params_df = pd.DataFrame([])
    params_df.index.name = 'index'


def simulate_set(desired_state, base, value, hours, markets, min_percentage_change):
    """ Just run 'simulate' for each hour in 'hours' and append the simulations_code
    All other parameters are the same except that the 1st hour is simulated
    twice, first with 'is_baseline' set to True as the baseline
    """
    timestamp = int(time.time())

    # First generate all simulation parameters and add them to params_csv
    is_baseline = True
    sim_params = series_from_params(timestamp, desired_state, base, value, min(hours), min_percentage_change,
                                    is_baseline)
    simulation_index = save_simulaton_params(sim_params)
    all_params_to_simulate = [(simulation_index,sim_params)]

    is_baseline = False
    for hour in hours:
        sim_params = series_from_params(timestamp, desired_state, base, value, hour, min_percentage_change, is_baseline)
        simulation_index = save_simulaton_params(sim_params)
        all_params_to_simulate.append((simulation_index, sim_params))

    # now just loop through those parameters and compute a simulation for each
    for simulation_index, sim_params in all_params_to_simulate:
        hour = sim_params['hour']
        markets.reset(seconds=config.ONEHOUR * hour)
        print 'Simulation Index: ', simulation_index
        simulate(markets, sim_params)


def index_from_params(sim_params):
    """ Return index corresponding to the parameters or None
    
    """
    temp_params = sim_params.copy()
    if 'timestamp' in temp_params:
        temp_params.drop('timestamp', inplace=True)

    for index, row in params_df.iterrows():
        if np.all(row.drop('timestamp') == temp_params):
            return index

    return None


def save_simulaton_params(sim_params):
    """
    Add a row to config.PARAMS csv with the parameters from this simulation:
    
    New row has columns 'hour', 'is_baseline', 'min_percentage_change', 'timestamp' and one boolean column for each
    possible currency
    
    :param desired_state: 
    :param hour: 
    :param is_baseline: 
    :return: 
    """
    global params_df

    index = index_from_params(sim_params)
    if index is None:
        # add data to config.PARAMS csv

        params_df = params_df.append(sim_params, ignore_index=True)
        params_df.to_csv(config.PARAMS)
        index = params_df.index[-1]

    sim_params.name = index
    return index


def simulate(markets, sim_params):
    """
    
    Simulates data according to the parameters in params_df.loc[sim_index]. Writes simulation to config.DATAFOLDER under
    <sim_index>.csv
    If <sim_index>.csv exists, it extends by appending more rows to it
    
    
    :param markets: 
    :param sim_params: pd.Series 
    :return: 
    """
    csv_filename = os.path.join(config.DATAFOLDER, '{0}.csv'.format(sim_params.name))

    if os.path.isfile(csv_filename):
        print 'csv found:', csv_filename
        data = pd.read_csv(csv_filename)

        # advance market iterator until 'time' exceeds the last time in 'data'
        last_time = data['time'].iloc[-1]
        markets.reset(current_time=last_time, seconds=sim_params['hour'] * config.ONEHOUR)

        # update original_portfolio to be the last step in the simulation. This is the portfolio we have to modify in
        # the next step
        current_portfolio = portfolio_from_simulation(sim_params.name, last_time)
    else:
        data = pd.DataFrame([], columns=['time'])  # other columns will be added but right now we just need 'time'
        current_portfolio = portfolio.Portfolio.from_simulation_params(markets.first_market(), sim_params)

    write_file = False

    for market in markets:
        print "simulating:", market.time
        write_file = True
        data = simulate_step(current_portfolio, market, data, sim_params)

    if write_file:
        print "Saving {0}".format(csv_filename)
        data.to_csv(csv_filename, index=False)


def portfolio_from_simulation(sim_index, time):
    """
    Load the current portoflio for the given parameters
    
    :param sim_index: points to <sim_index>.csv file with simulation data
    :param time: row of simulation csv to extract portfolio.Portfolio from
    :return: 
    """
    csv_filename = os.path.join(config.DATAFOLDER, "{sim_index}.csv".format(sim_index=sim_index))
    data = pd.read_csv(csv_filename)
    row = data[data['time']==time]
    dataframe = row.drop(['time', 'value'], axis=1).T

    dataframe.columns = ['Balance']
    dataframe.loc[:, 'Available'] = dataframe['Balance']
    dataframe.loc[:, 'Pending'] = 0

    p = portfolio.Portfolio(dataframe)
    return p


def simulate_step(current_portfolio, market, data, sim_params):
    """ Do one stop of the simulation for the given parameters
    
    Writes files:
    config.DATAFOLDER/<sim_index>.csv with 'time', 'value', <currency1>, <currency2>, ..., <currencyN> columns
    """
    # try to load dataframe from config.DATAFOLDER/<index>.csv,
    # TODO this should move outside this function
    """

    markets.reset(seconds=3600 * hour)
    if current_time in data['time']:
        # don't simulate this step, we already have and the result is in the row with 'time' = current_time
        p.dataframe['Balance'] = data[data['time']==current_time].drop('time', 'value')
    data.to_csv(csv_filename, index=False)
    """

    time = market.time
    min_percentage_change = sim_params['min_percentage_change']
    is_baseline = sim_params['is_baseline']
    # we need to compute this step of simulation
    if is_baseline:
        pass
    else:
        desired_state = desired_state_from_params(sim_params)
        current_portfolio.rebalance(market, desired_state, ['BTC'], min_percentage_change)

    value = current_portfolio.total_value(market, ['USDT', 'BTC'])
    s = current_portfolio.dataframe['Balance']
    s['time'] = time
    s['value'] = value

    data = data.append(s, ignore_index=True)
    return data


def desired_state_from_params(sim_params):
    """ Generate a 'state' from all the currencies in the simulation
    
    We are getting the currencies from the params_df, where currencies happen in the index (there are other things in
    the index as well). To get the currencies in the simulation we first remove everything in the index that is not
    a currency and then keep only those currencies that are set (have value equal to True)
    """
    assert type(sim_params) == pd.Series

    currencies = [p for p in sim_params.index if sim_params[p] and p not in config.PARAMS_INDEX_THAT_ARE_NOT_CURRENCIES]

    return portfolio.state_from_currencies(currencies)



'''
def fix_csv():
    """
    Load the csv and fix it, modify as needed
    :return: 
    """
    df = pd.read_csv(config.PARAMS)

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

def series_from_params(timestamp, desired_state, base, value, hour, min_percentage_change, is_baseline):

    # start sim_params with all currencies set to 0
    currencies = exchange.currencies_df().index.tolist()
    data_dict = {c:0 for c in currencies}
    data_dict.update({'timestamp': timestamp,
                      'hour': hour,
                      'is_baseline': is_baseline,
                      'min_percentage_change': min_percentage_change,
                      'base': base,
                      'value': value,
                      'N': portfolio.n_from_state(desired_state)})
    sim_params = pd.Series(data_dict)
    sim_params.update(desired_state['Weight'])

    return sim_params

