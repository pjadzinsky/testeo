import os

ONEHOUR = 3600
ONEDAY = 86400.0
FOLDER = os.path.expanduser('~/Testeo/simulations_data/')
PARAMS = os.path.join(FOLDER, 'params.csv')
DATAFOLDER = os.path.join(FOLDER, 'usd')
PARAMS_INDEX_THAT_ARE_NOT_CURRENCIES = ['N', 'time', 'value', 'timestamp', 'hour', 'min_percentage_change',
                                        'is_baseline', 'base', 'value']
