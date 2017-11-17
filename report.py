#!/usr/bin/python
import os
import tempfile

import pandas as pd

import bittrex_utils
import config
from market import market
from portfolio import portfolio
import state
import s3_utils


def report(market, portfolio, state):
    portfolio.to_s3(market.time)
    trading_value(market, portfolio)
    bitcoin_value(market)
    holding_value(market)
    #plot()


def plot():
    # TODO needs to be re-written
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


def recompute():
    """
    Get all portfolios stored in PORTFOLIOS_BUCKET, and recompute csvs
    in RESULTS_BUCKET
    
    :return: 
        None
    :uploads:
        csvs in RESULTS_BUCKET will be regenerated
        csvs are:
        <account>/bitcoin.csv   has columns time, BTC and USD.
                                BTC: the net amount of bitcoin deposited into the account
                                USD: the value of those bitcoins at that time
        
        <account>/trading.csv   has columns time, BTC and USD.
                                BTC: the value of the portfolio in BTC at that point in time
                                USD: the value of the portfolio in USD at that point in time
                                
        <account>/holding.csv   has columns time, BTC and USD.
                                BTC: the value of the original portfolio in BTC at that point in time
                                USD: the value of the original portfolio in USD at that point in time
                    
    """
    bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)
    all_summaries = bucket.objects.all()
    for summary in all_summaries:
        if os.environ['BITTREX_ACCOUNT'] in summary.key:
            p = portfolio.Portfolio.from_s3_key(summary.key)
            time = int(summary.key.rstrip('.csv').split('/')[-1])
            m = market.Market.at_time(time, 3600)
            report(m, p, None)


def clean():
    """
    First delete all files in RESULTS_BUCKET. Then 
    :return: 
        None
    """
    bucket = config.s3_client.Bucket(config.RESULTS_BUCKET)
    all_summaries = bucket.objects.all()
    objects = [{'Key': summary.key} for summary in all_summaries if os.environ['BITTREX_ACCOUNT'] in summary.key]
    if objects:
        bucket.delete_objects(Delete={'Objects': objects})


def bitcoin_value(market):
    """
        create <account>/bitoin.csv, the csv will have columns
            time, BTC and USD, where.
                BTC: the net value of bitcoins deposited into the account
                USD: the value of the bitcoins in USD as per 'market'
    :param market: 
    :return: 
    """
    time = market.time

    btc_value = 0
    response = bittrex_utils.client.get_deposit_history(currency='BTC')
    for transaction_dict in response['result']:
        btc_value += transaction_dict['Amount']

    response = bittrex_utils.client.get_withdrawal_history(currency='BTC')
    for transaction_dict in response['result']:
        btc_value -= transaction_dict['Amount']

    usd_value = btc_value * market.currency_chain_value(['USDT', 'BTC'])
    s = pd.Series({'time': time, 'BTC': btc_value, 'USD': usd_value})
    updated = s3_utils.update_csv(s, config.RESULTS_BUCKET, 'bitcoin')
    return updated


def holding_value(market):
    """
        create <account>/holding.csv, the csv will have columns
            time, BTC and USD, where.
                BTC: the value of the portfolio in BTC at that point in time
                USD: the value of the portfolio in USD at that point in time
                    
    
    :param market: 
    :return: 
    """
    time = market.time

    try:
        portfolio_creation_time, _ = state.previous_state(market.time)
        p = portfolio.Portfolio.at_time(portfolio_creation_time, 3600)
        btc_value = p.total_value(market, ['BTC'])
        usd_value = p.total_value(market, ['USDT', 'BTC'])

        s = pd.Series({'time': time, 'BTC': btc_value, 'USD': usd_value})
        updated = s3_utils.update_csv(s, config.RESULTS_BUCKET, 'holding')
        return updated
    except:
        return None


def trading_value(market, current_portfolio):
    """
        create <account>/trading.csv, the csv will have columns
            time, BTC and USD, where.
                BTC: the value of the original portfolio in BTC at that point in time
                USD: the value of the original portfolio in USD at that point in time
                    
    
    :param market: 
    :return: 
    """
    time = market.time

    btc_value = current_portfolio.total_value(market, ['BTC'])
    usd_value = current_portfolio.total_value(market, ['USDT', 'BTC'])

    s = pd.Series({'time': time, 'BTC': btc_value, 'USD': usd_value})
    updated = s3_utils.update_csv(s, config.RESULTS_BUCKET, 'trading')
    return updated

if __name__ == "__main__":
    clean()
    recompute()
