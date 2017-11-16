import os
import tempfile
import time

from pandas.util import testing
import numpy as np
import pandas as pd

import config

def update_state(time_sec, desired_state):
    """
    Update json file in bucket config.STATES_BUCKET 
    the json file has a dictionary linking time_sec to another dictionary linking currencies and their weights
    
    :param time_sec:
    """
    states = get_states()
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
        s3_key = "{account}/states.json".format(account=os.environ['BITTREX_ACCOUNT'])
        bucket.upload_file(temp, s3_key)


def get_states():
    bucket = config.s3_client.Bucket(config.STATES_BUCKET)
    s3_key = "{account}/states.json".format(account=os.environ['BITTREX_ACCOUNT'])

    _, temp = tempfile.mkstemp()
    try:
        bucket.download_file(s3_key, temp)
        states = pd.read_json(temp)
    except:
        states = pd.DataFrame([])

    return states

def frames_are_equal(left, right):
    left.sort_index(inplace=True)
    right.sort_index(inplace=True)
    try:
        testing.assert_frame_equal(left, right)
        return True
    except AssertionError:
        return False


def last_state():
    """ Return the time stamp and state associated with the last 'state' change
    """
    return previous_state(time.time())


def previous_state(time_sec):
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

