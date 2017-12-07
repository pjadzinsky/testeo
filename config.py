import os

import boto3
print 'Finished with imports in', __file__

ONEHOUR = 3600
ONEDAY = 86400.0
FOLDER = os.path.expanduser('~/Testeo/simulations_data/')
PARAMS = os.path.join(FOLDER, 'params.csv')
DATAFOLDER = os.path.join(FOLDER, 'usd')
PARAMS_INDEX_THAT_ARE_NOT_CURRENCIES = ['N', 'time', 'value', 'timestamp', 'hour', 'min_percentage_change',
                                        'is_baseline', 'base', 'value']

BUY_ORDERS_BUCKET = 'bittrex-buy-orders'
PORTFOLIOS_BUCKET = 'bittrex-portfolios'
RESULTS_BUCKET = 'bittrex-results'
STATES_BUCKET = 'bittrex-states'


if os.environ['LOGNAME'] == 'pablo':
    boto3.setup_default_session(profile_name='user2')
    session = boto3.Session(profile_name='user2')
else:
    boto3.setup_default_session()
    session = boto3.Session()

s3_client = boto3.resource('s3', 'us-west-2')
kms_client = session.client('kms', 'us-west-2')

