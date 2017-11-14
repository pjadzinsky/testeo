import os
import tempfile

import pandas as pd

import bittrex_utils
import config
from market import market
from portfolio import portfolio
import s3_utils


def report():
    print '*' * 80
    print 'BITTREX_ACCOUNT:', os.environ['BITTREX_ACCOUNT']

    import pudb
    pudb.set_trace()
    current_market = market.Market.from_bittrex()

    p = portfolio.Portfolio.account_last()
    p.report_value(current_market, 'trading.csv')

    total_bitcoin = total_bitcoin_deposit()
    s = pd.Series({'time': current_market.time, 'BTC': total_bitcoin})
    s3_utils.update_csv(s, config.RESULTS_BUCKET, 'bitcoins.csv')

    total_usd = total_USD_deposit(current_market)
    s = pd.Series({'time': current_market.time, 'USD': total_usd})
    s3_utils.update_csv(s, config.RESULTS_BUCKET, 'usd.csv')

    #plot()


def plot():
    import holoviews as hv
    hv.extension('bokeh')
    holding_df = s3_utils.get_df(config.RESULTS_BUCKET, 'holding.csv')
    trading_df = s3_utils.get_df(config.RESULTS_BUCKET, 'trading.csv')
    bitcoin_df = s3_utils.get_df(config.RESULTS_BUCKET, 'bitcoin.csv')
    usd_df = s3_utils.get_df(config.RESULTS_BUCKET, 'usd.csv')

    days_dim = hv.Dimension('Days')
    # convert to days
    t0 = trading_df.loc[0, 'time']
    #holding_df.loc[:, 'time'] = (holding_df['time'] - t0) / 86400
    trading_df.loc[:, 'time'] = (trading_df['time'] - t0) / 86400
    bitcoin_df.loc[:, 'time'] = (bitcoin_df['time'] - t0) / 86400
    usd_df.loc[:, 'time'] = (usd_df['time'] - t0) / 86400

    curve_opts = dict(line_width=2)
    #my_object = \ #hv.Curve(holding_df, label='holding').opts(style=curve_opts) * \
    my_object = hv.Curve((trading_df['time'], trading_df['BTC']), label='trading').opts(style=curve_opts) * \
                hv.Curve((bitcoin_df['time'], bitcoin_df['BTC']), label='bitcoin').opts(style=curve_opts)
                #hv.Curve(usd_df, label='usd').opts(style=curve_opts)

    renderer = hv.renderer('bokeh').instance()
    _, temp = tempfile.mkstemp()
    renderer.save(my_object, temp, style=dict(Image={'cmap':'jet'}))

    # upload html to s3
    s3_key = "{account}/plot.html".format(account=os.environ['BITTREX_ACCOUNT'])
    bucket = config.s3_client.Bucket(config.RESULTS_BUCKET)
    bucket.upload_file(temp, s3_key)



def total_bitcoin_deposit():
    total_btc = 0
    response = bittrex_utils.client.get_deposit_history(currency='BTC')
    for transaction_dict in response['result']:
        total_btc += transaction_dict['Amount']

    response = bittrex_utils.client.get_withdrawal_history(currency='BTC')
    for transaction_dict in response['result']:
        total_btc -= transaction_dict['Amount']

    return total_btc


def total_USD_deposit(market):
    # compute approximate total USD value of bitcoins just added/subtracted from the account
    bucket = config.s3_client.Bucket(config.RESULTS_BUCKET)
    s3_key = '{account}/bitcoin.csv'.format(account=os.environ['BITTREX_ACCOUNT'])
    print s3_key
    object = bucket.Object(s3_key)
    _, temp = tempfile.mkstemp()
    object.download_file(temp)
    df = pd.read_csv(temp, comment='#')
    df_at_time = df[df['time']==market.time]
    row = df_at_time.index[0]

    if df_at_time.empty:
        bitcoins_added = df.loc[0, 'BTC']
    else:
        bitcoins_added = df.loc[row, 'BTC'] - df.loc[row - 1, 'BTC']

    usd = bitcoins_added * market.currency_chain_value(['USDT', 'BTC'])
    return usd


