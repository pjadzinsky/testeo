#!/usr/bin/python
import time

import pandas as pd

import market
import state


def main(json_input, context):
    """
    
    :param N: Number of currencies to return
    :param markets_distance: distsance in seconds in between market conditions used
    :param rolling_window_size: How many points to take into accouont when computing volume and variance.
                                Total time considered is rolling_window_size * markets_distance
    :return: 
    """
    N = 12
    markets_distance = 3600
    rolling_window_size = 7 * 24    # one week when markets_distance is one_hour
    timestamp = int(time.time())
    markets = market.Markets(markets_distance, 0, start_time=timestamp - rolling_window_size * markets_distance)

    print 'Estimating best currencies with {} markets'.format(len(markets.times))

    volumes = markets.stats_volume()
    print '*' * 80
    print 'market volumes'
    print volumes.head(20)

    variance_df = markets.stats_variance(rolling_window_size)
    mean_variance = variance_df.mean(axis=0)

    mean_variance.sort_values(ascending=False, inplace=True)
    print mean_variance.head(20)
    print mean_variance.index.values[:30]
    print '*' * 80

    print type(volumes), type(mean_variance)
    df = pd.concat([volumes, mean_variance], axis=1)
    df.columns = ['volume', 'variance']
    df = df[df['volume'] > 1E6]
    df = df.sort_values('variance', ascending=False)
    print ','.join(df.index.values[:N])
    currencies = df.index.tolist()[:N]

    # save state to s3
    new_state = state.from_currencies(currencies)
    state.save(timestamp, new_state)



if __name__ == "__main__":
    main(0, 0)
