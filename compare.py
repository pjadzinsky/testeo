#!/usr/bin/python
import os
import sys

import gflags
import holoviews as hv
import pandas as pd

from market import market
from portfolio import portfolio
import bittrex_utils
import config
import report
import s3_utils
import state

hv.extension('bokeh')

def main():
    holding_usd = 0
    trading_usd = 0
    bitcoin_usd = 0
    holding_btc = 0
    trading_btc = 0
    bitcoin_btc = 0

    for account in ['gaby', 'pablo']:
        if account == 'gaby':
            os.environ['BITTREX_SECRET_ENCRYPTED'] = os.environ['BITTREX_SECRET_GABY_ENCRYPTED']
            os.environ['BITTREX_KEY_ENCRYPTED'] = os.environ['BITTREX_KEY_GABY_ENCRYPTED']
        elif account == 'pablo':
            os.environ['BITTREX_SECRET_ENCRYPTED'] = os.environ['BITTREX_SECRET_PABLO_ENCRYPTED']
            os.environ['BITTREX_KEY_ENCRYPTED'] = os.environ['BITTREX_KEY_PABLO_ENCRYPTED']

        reload(bittrex_utils)
        os.environ['BITTREX_ACCOUNT'] = account
        print '*' * 80
        print 'BITTREX_ACCOUNT:', account

        print "This is the original Portfolio"

        current_portfolio = portfolio.Portfolio.from_bittrex()
        portfolio_change = report.portfolio_change(current_portfolio)
        print portfolio_change

        bitcoin_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/bitcoin.csv'.format(account=os.environ['BITTREX_ACCOUNT']))
        print '*' * 8
        print 'bitcoin_df'
        print bitcoin_df
        trading_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/trading.csv'.format(account=os.environ['BITTREX_ACCOUNT']))
        print '*' * 8
        print 'trading_df'
        print trading_df
        holding_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/holding.csv'.format(account=os.environ['BITTREX_ACCOUNT']))
        print '*' * 8
        print 'holding_df'
        print holding_df

        holding_usd += holding_df['USD'].values[-1]
        trading_usd += trading_df['USD'].values[-1]
        bitcoin_usd += bitcoin_df['USD'].values[-1]
        holding_btc += holding_df['BTC'].values[-1]
        trading_btc += trading_df['BTC'].values[-1]
        bitcoin_btc += bitcoin_df['BTC'].values[-1]
    print 'holding_usd:', holding_usd
    print 'trading_usd:', trading_usd
    print 'bitcoin_usd:', bitcoin_usd
    print 'holding_btc:', holding_btc
    print 'trading_btc:', trading_btc
    print 'bitcoin_btc:', bitcoin_btc
    print '*' * 80
    print 'Ratio trading/holding (usd):', trading_usd / holding_usd
    print 'Ratio trading/bitcoin (usd):', trading_usd / bitcoin_usd
    print '*' * 80
    print 'Ratio trading/holding (BTC):', trading_btc / holding_btc
    print 'Ratio trading/bitcoin (BTC):', trading_btc / bitcoin_btc


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


