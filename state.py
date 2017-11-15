import os
import tempfile

from pandas.util import testing
import numpy as np
import pandas as pd

import config

def update_state(time_sec, desired_state):
    """
    Update json file in bucket config.STATES_BUCKET 
    the json file has a dictionary linking time_sec to another dictionary linking currencies and their weights
    
    :param time_sec:
    :param desired_state: 
    :return: 
    """

    bucket = config.s3_client.Bucket(config.STATES_BUCKET)
    s3_key = "{account}/states.json".format(account=os.environ['BITTREX_ACCOUNT'])

    _, temp = tempfile.mkstemp()
    try:
        bucket.download_file(s3_key, temp)
        states = pd.read_json(temp)
        last_row = states.iloc[-1]
        last_state = pd.DataFrame(last_row.state)
    except:
        states = pd.DataFrame([])
        last_state = None

    if last_state is None or not frames_are_equal(last_state, desired_state):
        s = pd.Series({'time': time_sec, 'state': desired_state})
        states = states.append(s, ignore_index=True)
        states.to_json(temp)

        bucket.upload_file(temp, s3_key)


def frames_are_equal(left, right):
    left.sort_index(inplace=True)
    right.sort_index(inplace=True)
    try:
        testing.assert_frame_equal(left, right)
        return True
    except AssertionError:
        return False



