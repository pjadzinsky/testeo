import os
import time

from pandas.util import testing
import numpy as np
import pandas as pd

import config
import s3_utils
print 'Finished with imports in', __file__


def frames_are_equal(left, right):
    """
    
    Return True if 'left' and 'right' represent the same state, False otherwise
    
    Because some states include BTC (and/or ETH) and some states don't but they use this currency as an intermediate
    step, there might be BTC (or ETH) in one of the dataframes but not the other.
    
    If the only difference in 'left'/'right' is in BTC (or ETC) consider the states equal. THIS IS NOT IMPLEMENTED
    I have not only to look at the currencies in the portfolio ut adjust the weights once this currency is removed
    :param left: 
    :param right: 
    :return: 
    """
    left.sort_index(inplace=True)
    right.sort_index(inplace=True)
    try:
        testing.assert_frame_equal(left, right)
        return True
    except AssertionError:
        return False


def current():
    return at_time(time.time())


def at_time(time_sec):
    """ Return the 'state' that was desired at 'time_sec' and the time when it was first defined
    
    The 'state' is defined by a file (if it exists) in BITTREX_STATES under <account>/<time_stamp>.csv
    and where the time_stamp is the closest one to time_sec that is also less than time_sec
    
    If STATES_BUCKET doesn't have a csv corresponding to a time before 'time_sec', retrun None, None
    """
    bucket = config.s3_client.Bucket(config.STATES_BUCKET)
    all_summaries = bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])

    delta = np.inf
    state_timestamp = None
    state = None
    s3_key = None

    for summary in all_summaries:
        if summary.key.endswith('.csv'):
            timestamp = int(summary.key.split('/')[1].replace('.csv', ''))
            if timestamp <= time_sec and time_sec - timestamp < delta:
                state_timestamp = timestamp
                delta = time_sec - timestamp
                s3_key = summary.key

    if s3_key:
        state = s3_utils.get_df(config.STATES_BUCKET, s3_key, index_col=0)

    return state_timestamp, state


def from_previous_buy_order(time):
    orders_bucket = config.s3_client.Bucket(config.BUY_ORDERS_BUCKET)

    all_summaries = orders_bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])

    time_diff = np.inf
    best_key = None
    state = None
    state_time = None
    for summary in all_summaries:
        # key is of the form <account>/<time_stamp>_buy_df.csv
        # but as of 11/29/2017 we have a bug in production and there are order_buckets without "<account>/". That is
        # why I'm checking for <account> in the key explicitely
        order_time = int(summary.key.split('/')[1].split('_')[0])
        if order_time < time and time - order_time < time_diff:
            time_diff = time - order_time
            best_key = summary.key
            state_time = order_time

    if best_key:
        buy_order_df = s3_utils.get_df(orders_bucket.name, best_key, comment='#', index_col=0)
        currencies = buy_order_df[buy_order_df['target_currency'] > 0].index

        state = from_currencies(currencies)

    return state_time, state


def save(time_sec, state):
    """ If needed, save the 'state' associated with time_sec
    
    We'll only save parameter 'state' if the returned state by 'at_time(time_sec)' is different from 'state'
    (or if there is no 'state' at all)
    """


    _, other = at_time(time_sec)
    if other is None or not frames_are_equal(state, other):
        s3_key = '{account}/{time_sec}.csv'.format(account=os.environ['EXCHANGE_ACCOUNT'],
                                                   time_sec=time_sec)
        s3_utils.put_csv(state, config.STATES_BUCKET, s3_key)
        print '*' * 80
        print s3_key, 'Just saved'


def from_portfolio(p):
    return from_currencies(p.dataframe.index)


def from_largest_markes(market, N, include_usd):
    state = uniform_state(market, N, include_usd=include_usd)
    return state


def from_currencies(currencies):
    weights = 1.0 / len(currencies)
    state = pd.DataFrame({'Weight': weights}, index=currencies)
    return state


def random(currencies, N):
    """ Generate a random makret using 'N' currencies from 'currencies'
    """
    currencies_to_use = np.random.choice(currencies, size=N, replace=False)
    return from_currencies(currencies_to_use)


def uniform_state(market, N, include_usd=True, intermediates=['BTC', 'ETH']):
    """
    
    :param market: DataFrame with market conditions. The 'N' currencies with the most volume will be used to define a
        state
    :param N: number of cryptocurrencies to include
    :param currencies: dict linking currencies to the values of the 'state'
    :param include_usd: If true, usd will be added to the list of cryptocurrencies to hold (even though it is not).
    :return: Dataframe with the weight of each currency (1/N)
    """
    volumes_df = market.usd_volumes(intermediates)
    volumes_df.drop('USDT', axis=0, inplace=True)

    currencies = volumes_df.head(N).index.tolist()
    assert 'USDT' not in volumes_df.index
    if include_usd:
        currencies[-1] = 'USDT'

    state = pd.DataFrame([1. / N] * N, index=currencies, columns=['Weight'])

    return state


def currencies_from_state(state):
    currencies = state[state['Weight'] > 0].index.values
    return currencies


def n_from_state(state):
    return len(currencies_from_state(state))


'''
def last_state_old():
    """ Return the time stamp and state associated with the last 'state' change
    """
    return previous_state(time.time())


def previous_state_old(time_sec):
    """ Return the time stamp and state prior 'time_sec'
    """
    states = get_states()


    if states.empty:
        last_state = None
        last_time = None
    else:
        # find first time before 'time_sec'
        time_difference = (states['time'] - time_sec).values

        # we are looking for a time in 'states' before time_sec and so the largest time_difference that is still negative
        index = np.searchsorted(time_difference, 0) - 1
        row = states.iloc[index]
        last_time = row['time']
        last_state = pd.DataFrame(row['state'])

    return last_time, last_state


def update_state_old(time_sec, desired_state):
    """
    Update json file in bucket config.STATES_BUCKET 
    the json file has a dictionary linking time_sec to another dictionary linking currencies and their weights
    
    it only updates the files if desired_state is different from last entry
    
    :param time_sec:
    """
    states = get_states()

    if time_sec in states['time'].unique():
        return

    if states.empty:
        last_state = None
    else:
        last_row = states.iloc[-1]
        last_state = pd.DataFrame(last_row.state)

    if last_state is None or not frames_are_equal(last_state, desired_state):
        s = pd.Series({'time': time_sec, 'state': desired_state})
        states = states.append(s, ignore_index=True)
        _, temp = tempfile.mkstemp()
        states.to_json(temp)

        bucket = config.s3_client.Bucket(config.STATES_BUCKET)
        s3_key = "{account}/states.json".format(account=os.environ['EXCHANGE_ACCOUNT'])
        bucket.upload_file(temp, s3_key)


def get_states_old():
    bucket = config.s3_client.Bucket(config.STATES_BUCKET)
    s3_key = "{account}/states.json".format(account=os.environ['EXCHANGE_ACCOUNT'])

    _, temp = tempfile.mkstemp()
    try:
        bucket.download_file(s3_key, temp)
        print temp
        states = pd.read_json(temp)
        states.sort_values(['time'], inplace=True)
    except:
        states = pd.DataFrame([])

    # remove any duplicate entries
    states = states.groupby('time', as_index=False).first()
    states.reset_index(drop=True, inplace=True)

    return states
'''
