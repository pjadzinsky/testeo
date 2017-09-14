"""
Module to load and work with simulations

Simulation parameters are defined in simulations.csv and the simulations themselves in simulations/<index>.csv


"""

import os

import pandas as pd

SIMULATIONS = os.path.join(os.path.expanduser('~'), 'Testeo', 'results', 'data.csv')

class Simulations(object):
    def __init__(self):
        self.params = pd.read_csv(SIMULATIONS)
        print self.params.head()


