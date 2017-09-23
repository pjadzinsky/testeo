#!/usr/bin/python
"""
# On 09-21-2017 I started running 'update_simulations.py' that takes an already existing simulations and updates it
# by extending the simulation up to current times. Here I will delete all data after 09-19-2017 which is a time
# before the bug was introduced
"""
import os
import sys

import gflags
import pandas as pd

from market import market
from simulations_code import simulate
import config

FLAGS = gflags.FLAGS

def main():
    params_df = simulate.params_df

    t0 = 1505779200
    for index in params_df.index:
        import pudb
        pudb.set_trace()
        csv_name = os.path.join(config.DATAFOLDER, "{0}.csv".format(index))
        df = pd.read_csv(csv_name)
        df = df[df['time'] < t0]
        df.to_csv(csv_name, index=False)

if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError as e:
        print "%s\nUsage: %s ARGS\n%s" % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    main()
