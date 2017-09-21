"""
Module to load and work with simulations

Simulation parameters are defined in simulations.csv and the simulations themselves in simulations/<index>.csv


"""

import os

import pandas as pd
import holoviews as hv
import numpy as np

from simulations_code import simulate
import config


hv.extension('bokeh')
renderer = hv.Store.renderers['bokeh'].instance(fig='html')


class Simulations(object):
    def __init__(self):
        self.params_df = pd.read_csv(config.PARAMS, index_col=0)
        self.data = {}

        for index in self.params_df.index:
            self.data[index] = _load_data(index)
            _compute_mean_percentage(self.data[index])
            _compute_rate(self.data[index])


def load_all_values():
    """ Load all 'value' columns from all simulations into a big DataFrame indexed by 'time'.
    The name of each column is the index into "params_df" where we can get the simulation parameters from
    
    Each column has one simulation, there are potentially many NaNs per column since the 'index' in this DataFrame
    is the same for all simulations
    
    """
    df = pd.DataFrame([])
    for index in simulate.params_df.index:
        new_df = _load_data(index)

        if new_df is not None:
            # make time relative
            new_df.loc[:, 'time'] = new_df['time'] - new_df['time'].iloc[0]

            # index by 'time'
            new_df.set_index('time', drop=True, inplace=True)

            # extract just the 'value' column but as DF rather than just a series
            new_df = new_df[['value']]

            # change the name of the column for nice concatenation
            new_df.columns = [index]
            df = pd.concat([df, new_df], axis=1)

    return df


def _load_data(index):
    """ load the csv associated with the row.name as a dataframe
    csv to load is named "<row.name>.csv" and is store in config.DATAFOLDER
    """
    fname = os.path.join(config.DATAFOLDER, '{0}.csv'.format(index))
    if os.path.isfile(fname):
        data = pd.read_csv(fname)
    else:
        data = None

    return data


def compute_mean_percentage(data_df):
    return data_df.apply(_compute_mean_percentage, axis=0)


def compute_mean_rate(data_df):
    return data_df.apply(_compute_rate, axis=0)


def _compute_mean_percentage(data_series):
    """ Compute percentage of increase at every point in time
     
     row.data as a DataFrame with columns 'time' and 'value' we just compute the 'percentage' that value['time']
     represents with respect to value[0]
    
    :args: data (pd.DataFrame), with columns 'time' and 'value'
    """
    assert type(data_series) == pd.Series

    values = data_series.values
    first_value = values[0]
    times = data_series.index
    first_time = times[0]
    return (values - first_value) * 100.0 / first_value / (times - first_time)


def _compute_rate(data_series):
    """ Compute interest rate yielded by data at each point in time
    
    :args: data (pd.DataFrame), with columns 'time' and 'value'
    """
    assert type(data_series) == pd.Series

    values = data_series.values
    first_value = values[0]
    times = data_series.index
    first_time = times[0]

    days = (times - first_time) / config.ONEDAY
    # rate ** days = last_value / first_value
    # days * log(rate) = log(last_value / first_value)
    # rate = 10**(log(last_value / first_value) / days)

    rate = 10 ** (np.log10(values/first_value) / days)
    return rate


def currencies(row):
    """
    return a list with the currencies used in the simulation
    """
    # keep only boolean values
    boolean_row = row.select(lambda i: row[i])
    boolean_row.drop(['N', 'hour', 'timestamp', 'baseline'], inplace=True)
    if 'baseline' in boolean_row.index:
        boolean_row.drop('baseline', inplace=True)

    return boolean_row.index.tolist()


class Simulation(object):
    """
    A simulation is part of a simulation set. It is just defined by an index. The index is the row into 
    the PARAMS datafolder and <index>.csv with the time, value data
    """
    def __init__(self, index):
        self.index = index
        df = _load_data(index)
        #df.apply(_compute_rate, axis=1)
        #df.apply(_compute_mean_percentage, axis=1)
        self.df = df


#params_df.loc[:, 'data'] = params_df.apply(lambda x: Simulation(x.name), axis=1)

#params_df.apply(_compute_rate)               # work in place, adding column 'rate' to params_df.data
#params_df.apply(_compute_mean_percentage)    # work in place, adding column 'mean %' to params_df.data

'''
class SimulationSet(object):
    """ 
    A simulation is done choosing:
        a set of currencies randomly chosen
        a set of hours to perform rebalance every so often
        then fetching the markets and rebalancing
        All simulations_data for a given set of parameters are associated with a timestamp
        Here we load all those simulations_data and do whatever we want to do with them
        
    To define a SimulationSet we only need to define the 'timestamp' since that leads to all the raws in params_df
    and the indexes in params_df is what is needed to define Simulation
     """
    def __init__(self, timestamp):

        self.timestamp = timestamp
        self.load_data()    # adds self.data_dict dictionary

    def _indexes(self):
        return params_df[params_df['timestamp'] == self.timestamp].index.tolist()

    def load_data(self):
        """ Load and apply mean_percentage and rate to each Simulation object in the set.
        At some point we might need to take the computation out of here"""

        self.data_dict = {}
        for index in self._indexes():
            sim = Simulation(index)
            sim._compute_mean_percentage()
            sim._compute_rate()

            if sim.is_baseline():
                self.data_dict['baseline'] = sim
            else:
                self.data_dict[sim.hour()] = sim


    def load_params(self):
        all_params = params_df
        sim_set_params = all_params[all_params['timestamp'] == self.timestamp]

        return sim_set_params

    def add_sorting(df):
        """
        For each data set (the only thing that changes is time). Sort hours by some type of return and add value
        to df
        
        :param df: 
        :return: 
        """
        # Simulation set starts always with a 'baseline' data. If we pull the indexes of these 'baselines' then
        # have a handle onto the start of each data set.
        # to identify a data we can just look at rows with 'rebalanced' set to False
        baselines = df[df['rebalance']==False]
        baselines_index = baselines.index.tolist()

        # add to 'baselines_index' the index corresponding to the next empty row so that extracting all data for a
        # data is just extracting between baselines_index[i] and baselines_index[i+1]
        baselines_index.append(df.shape[0])

        for start, end in zip(baselines_index[:-1], baselines_index[1:]):
            temp = df.iloc[start:end]['rate']
            # I multiply by -1 to have them in descending order and '0' be the best data
            df.loc[start:end - 1, 'sorting'] = temp.rank(ascending=False)

        return df







def final_analysis():
    df = read_data()
    #_compute_mean_percentage(df)
    #_compute_rate(df)

    plot_result()

    # For each data set (the only thing that changes is time). Sort hours by some type of return. Then compute
    # the mean and std of the ordering of a given hour. Is 1hour the best?
    add_sorting(df)
    evaluate_hour()

    """
    Compute something like 'rate' in between start and "n" days into the data and then from "n" days until the end
    Then scatter 1st result vs last. Can we trust past behaviour as a predictar of immediate future one?
    """
    print df.head()
    print 1


def plot_result():
    """
    For each data condition (hour, all currencies) make a 2D plot with axis like 'mean %'
    and 'rate'. We can make one plot per 'N' or one single plot using different markers.
    
    :return: None, generates FOLDER / layout_1.html
    """
    import holoviews as hv
    hv.extension('bokeh')
    renderer = hv.Store.renderers['bokeh'].instance(fig='html')

    df = pd.read_csv(PARAMS)

    # we only plot 'rebalance' data
    df = df[df['rebalance']==True]

    # Create a dictionary linking 'N' to the corresponding Scatter plot
    holoMap = hv.HoloMap({N:hv.Scatter(df[df['N']==N], kdims=['rate'], vdims=['mean %']) for N in
                          [4, 8, 16]}, kdims=['N'])
    holoview = holoMap.select(N={4, 8, 16}).layout()
    renderer.save(holoview, os.path.join(FOLDER, 'layout_1'), sytle=dict(Image={'cmap':'jet'}))


    N_hour = product((4, 8, 16), (1, 2, 6, 12, 24))
    holoMap = hv.HoloMap({(N, h):hv.Scatter(df[(df['N']==N) & (df['hour']==h)], kdims=['rate'],
                                            vdims=['mean %']) for N, h in N_hour}
                         , kdims=['N', 'hour'])
    holoview_4 = holoMap.select(N={4}).overlay()
    holoview_8 = holoMap.select(N={8}).overlay()
    holoview_16 = holoMap.select(N={16}).overlay()
    holoview = holoview_4 + holoview_8 + holoview_16
    renderer.save(holoview, os.path.join(FOLDER, 'layout_2'), sytle=dict(Image={'cmap':'jet'}))



def evaluate_hour(N=None, currencies=None):
    """
    For each data set (the only thing that changes is time). Sort hours by some type of return. Then compute
    the mean and std of the ordering of a given hour. Is 1hour the best?
    
    :N: int, limit analysis to data with the given number of currencies
    :currencies: list of str, limit analysis to data that have those currencies. Len(currencies) can be less
                 than or equal to N, ie: if currencies = ['LTC'] then all data involving 'LTC' will be reported
                 
    :return: 
    """

    df = pd.read_csv(PARAMS)

    if N:
        assert type(N) == int
        df = df[df['N']==N]
        df.reset_index(inplace=True, drop=True)

    if currencies:
        assert type(currencies) == list
        df = df[df.apply(lambda x: np.alltrue([x[c] for c in currencies]), axis=1)]
        df.reset_index(inplace=True, drop=True)

    # to identify a data we can just look at rows with 'rebalanced' set to False

    baselines = df[df['rebalance']==False]
    baselines_index = baselines.index.tolist()

    # add to 'baselines_index' the index corresponding to the next empty row so that extracting all data for a
    # data is just extracting between baselines_index[i] and baselines_index[i+1]
    baselines_index.append(df.shape[0])

    output_df = pd.DataFrame([])

    for start, end in zip(baselines_index[:-1], baselines_index[1:]):
        temp = df.iloc[start:end]
        sim_name = csv_row_to_name(temp.iloc[0])
        sorted_order = np.argsort(temp['mean %'].values)
        reversed_order = len(sorted_order) - 1 - sorted_order
        hours = temp['hour'].values
        s = pd.Series(reversed_order, index=hours, name=sim_name)
        output_df = pd.concat([output_df, s], axis=1)

    mean = output_df.mean(axis=1)
    std = output_df.std(axis=1)
    hour_stats = pd.concat([mean, std], axis=1)
    hour_stats.columns = ['mean', 'std']

    hour_stats.to_csv(os.path.join(FOLDER, 'hour_stats.csv'))

    return hour_stats


params_df.loc[:, 'data'] = params_df.apply(lambda x: Simulation(x.name), axis=1)
'''
def plot_in_time(data):
    """ TO start with, we jut plot 'baseline' and each 'hour' simulation
    """
    dict_spec = {'Curve': {'width': 600, 'height':600}}
    # Create a dictionary linking 'N' to the corresponding Scatter plot
    return hv.Curve(data)

    holoMap = hv.HoloMap({column:hv.Scatter(data[column]), kdims=['name'], vdims=['time']) for N in data.columns})
    holoview_4 = holoMap.select(N={4}).overlay()
    holoview_8 = holoMap.select(N={8}).overlay()
    holoview_16 = holoMap.select(N={16}).overlay()
    holoview = holoview_4 + holoview_8 + holoview_16
    renderer.save(holoview, os.path.join(FOLDER, 'layout_2'), sytle=dict(Image={'cmap':'jet'}))
    """
