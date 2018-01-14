#!/usr/bin/python
import os
import sys

import gflags
import pandas as pd

import config
from portfolio import portfolio
from simulations_code import simulate

FLAGS = gflags.FLAGS

def fix1():
    """
    # On 09-21-2017 I started running 'update_simulations.py' that takes an already existing simulations and updates it
    # by extending the simulation up to current times. Here I will delete all data after 09-19-2017 which is a time
    # before the bug was introduced
    """
    params_df = simulate.params_df

    t0 = 1505779200
    for index in params_df.index:
        csv_name = os.path.join(config.DATAFOLDER, "{0}.csv".format(index))
        df = pd.read_csv(csv_name)
        df = df[df['time'] < t0]
        df.to_csv(csv_name, index=False)


def fix2():
    """
    On 09-23-2017 I'm adding 'N' to params_df, the number of currencies used in the simulation
    """
    params_df = simulate.params_df

    for index, row in params_df.iterrows():
        desired_state = simulate.desired_state_from_params(row)
        params_df.loc[index, 'N'] = portfolio.n_from_state(desired_state)

    params_df.to_csv('test.csv')

if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    fix2()
