"""
Module to load and work with simulations

Simulation parameters are defined in simulations.csv and the simulations themselves in simulations/<index>.csv


"""

import os

import pandas as pd
import numpy as np

from simulations_code import simulate


PARAMS_DF = pd.read_csv(simulate.PARAMS, index_col=0)

class SimulationSet(object):
    """ 
    A simulation is given by:
        a set of currencies randomly chosen
        a set of hours to perform rebalance every so often
        then fetching the markets and rebalancing
        All simulations_data for a given set of parameters are associated with a timestamp
        Here we load all those simulations_data and do whatever we want to do with them
     """
    def __init__(self, timestamp):

        self.timestamp = timestamp
        self.params_df = self.load_params()
        self.N = self.get_N()
        self.baseline_index = self.params_df.index[0]
        self.rebalance_indexes = self.params_df.index[1:].tolist()

        print self.N
        print self.get_hours()
        print self.get_rebalance()
        print "baseline index", self.baseline_index
        print "rebalanced indexes", self.rebalance_indexes

    def load_params(self):
        all_params = PARAMS_DF
        sim_set_params = all_params[all_params['timestamp'] == self.timestamp]

        return sim_set_params

    def get_N(self):
        """ 
        :return: Return the number of currencies used in the simulation. All entries with the same 'timestamp'
        should have the same 'N'
        """
        Ns = self.params_df['N']
        Ns_set = set(Ns)
        assert len(Ns_set) == 1
        return Ns_set.pop()

    def get_hours(self):
        return self.params_df['hour']

    def get_rebalance(self):
        return self.params_df['rebalance']

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


class Simulation(object):
    """
    A simulation is part of a simulation set. It is just defined by an index. The index is the row into 
    the PARAMS datafolder and <index>.csv with the time, value data
    """
    def __init__(self, index):
        self.index = index
        self.data = _load_data(index)
        """
        self.baseline_index = self._get_baseline_index()
        self.baseline = None
        # careful, baseline_index could be 0
        if self.baseline_index is not None:
            self.baseline = _load_data(self.baseline_index)
        """

    def is_baseline(self):
        # 'rebalance' is set to False in 'baseline'
        # PARAMS_DF reads False as 0.0
        return not PARAMS_DF.loc[self.index, 'rebalance']

    def _get_baseline_index(self):
        """ If this item is not a 'baseline' simultion, get the first row above 'self.index' that has 
        'rebalance' set to True
        """
        if self.is_baseline():
            index = None
        else:
            temp = self.index
            while True:
                temp -= 1
                if PARAMS_DF.loc[temp, 'rebalance'] == False:
                    # baseline found
                    index = temp
                    break

                if temp < 0:
                    raise RuntimeError

        return index

    def compute_mean_percentage(self):
        """ Compute percentage of increase last 'result' value has when compared to 'baseline' at the same time
        
        :args: data (pd.DataFrame), with columns time and value
        """
        times = self.data.time.values
        values = self.data.value.values
        self.data.loc[:, 'mean %'] = (values - values[0]) * 100.0 / values[0] / (times - times[0])


    def compute_rate(self):
        """ Compute interest rate yielded by data at each point in time
        
        :args: data (pd.DataFrame), with columns time and value
        """
        days = self.data['time'].values
        values = self.data['value'].values

        # rate ** days = last_value / first_value
        # days * log(base) = log(last_value / first_value)
        # base = 10**(log(last_value / first_value) / days)
        rate = 10 ** (np.log10(values/values[0]) / (days - days[0]))
        self.data.loc[:, 'rate'] = rate

    def simulation_name(currencies, hours, min_percentage_change, suffix=None):
        """
        Return a string with all parameters used in the data
        
        :return: 
        """
        if currencies:
            name = "names_" + '_'.join(currencies) + \
                   "_hours_" + "_".join([str(h) for h in hours]) + \
                   "_%change_" + str(int(min_percentage_change * 100))
        if suffix:
            name += suffix

        return name

    def params(self):
        return PARAMS_DF.loc[self.index]

    def timestamp(self):
        return self.params()['timestamp']

    def hour(self):
        return self.params()['hour']

    def currencies(self):
        """
        return a list with the currencies used in the simulation
        """
        # keep only boolean values
        row = self.params()
        boolean_row = row.select(lambda i: row[i])
        boolean_row.drop(['N', 'hour', 'timestamp', 'rebalance'], inplace=True)
        if 'rebalance' in boolean_row.index:
            boolean_row.drop('rebalance', inplace=True)

        return boolean_row.index.tolist()





def final_analysis():
    df = read_data()
    #compute_mean_percentage(df)
    #compute_rate(df)

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

def _load_data(index):
    fname = os.path.join(simulate.DATAFOLDER, '{0}.csv'.format(index))
    return pd.read_csv(fname)
