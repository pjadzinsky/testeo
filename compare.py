#!/usr/bin/python
import os
import sys

import gflags
import holoviews as hv
import pandas as pd

import config
import bittrex_utils
from market import market
from portfolio import portfolio
import s3_utils

hv.extension('bokeh')

def main():
    for account in ['gaby', 'pablo']:
        """
        if account == 'gaby':
            os.environ['BITTREX_SECRET_ENCRYPTED'] = os.environ['BITTREX_SECRET_GABY_ENCRYPTED']
            os.environ['BITTREX_KEY_ENCRYPTED'] = os.environ['BITTREX_KEY_GABY_ENCRYPTED']
        elif account == 'pablo':
            os.environ['BITTREX_SECRET_ENCRYPTED'] = os.environ['BITTREX_SECRET_PABLO_ENCRYPTED']
            os.environ['BITTREX_KEY_ENCRYPTED'] = os.environ['BITTREX_KEY_PABLO_ENCRYPTED']
        import pudb
        pudb.set_trace()
        reload(bittrex_utils)
        """
        os.environ['BITTREX_ACCOUNT'] = account

        bitcoin_df = s3_utils.get_df(config.RESULTS_BUCKET, 'bitcoin.csv')
        print '*' * 8
        print 'bitcoin_df'
        print bitcoin_df
        trading_df = s3_utils.get_df(config.RESULTS_BUCKET, 'trading.csv')
        print '*' * 8
        print 'trading_df'
        usd_df = s3_utils.get_df(config.RESULTS_BUCKET, 'usd.csv')
        print '*' * 8
        print 'usd_df'

        print '*' * 80
        print 'Current value trading is: {}(USD)'.format(trading_df['USD'].values[-1])
        print 'Current value usd is: {}(USD)'.format(usd_df['USD'].values[-1])
        print 'Current value trading is: {}(BTC)'.format(trading_df['BTC'].values[-1])
        print 'Current value bitcoin is: {}(BTC)'.format(bitcoin_df['BTC'].values[-1])

        """
        print 'trading/holding ratio is: ', trading_value / holding_value
        print 'trading/bitcoin ratio is: ', trading_value / bitcoin_value
        plot()
        """

def plot():
    holding_df = pd.read_csv(os.path.expanduser('~/Testeo/results/Portfolio_1/holding.csv'))
    trading_df = pd.read_csv(os.path.expanduser('~/Testeo/results/Portfolio_1/trading.csv'))
    bitcoin_df = pd.read_csv(os.path.expanduser('~/Testeo/results/Portfolio_1/bitcoins.csv'))

    days_dim = hv.Dimension('Days')
    # convert to days
    t0 = holding_df.loc[0, 'time']
    holding_df.loc[:, 'time'] = (holding_df['time'] - t0) / 86400
    trading_df.loc[:, 'time'] = (trading_df['time'] - t0) / 86400
    bitcoin_df.loc[:, 'time'] = (bitcoin_df['time'] - t0) / 86400

    curve_opts = dict(line_width=2)
    my_object = hv.Curve(holding_df, label='holding').opts(style=curve_opts) * \
                hv.Curve(trading_df, label='trading').opts(style=curve_opts) * \
                hv.Curve(bitcoin_df, label='bitcoin').opts(style=curve_opts)

    renderer = hv.renderer('bokeh').instance()
    renderer.save(my_object, 'example_I', style=dict(Image={'cmap':'jet'}))

if __name__ == "__main__":
    main()


