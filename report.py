#!/usr/bin/python
import os
import tempfile

import holoviews as hv
import pandas as pd

import bittrex_utils
import config
from market import market
from portfolio import portfolio
import state
import s3_utils

hv.extension('bokeh')


def report(market, portfolio, state):
    portfolio.to_s3(market.time)
    state.update_state()
    portfolio_change(portfolio)
    trading_value(market, portfolio)
    bitcoin_value(market)
    holding_value(market)
    plot()


ONEDAY = 86400      # seconds in a day
def plot():
    renderer = hv.renderer('bokeh').instance(fig='html')
    in_bitcoins_df = pd.DataFrame([], columns=['holding', 'trading', 'bitcoin'])
    in_usd_df = pd.DataFrame([], columns=['holding', 'trading', 'bitcoin'])

    for account in ['pablo', 'gaby']:
        holding_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/holding.csv'.format(account=account),
                                     index_col=2)
        trading_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/trading.csv'.format(account=account),
                                     index_col=2)
        bitcoin_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/bitcoin.csv'.format(account=account),
                                     index_col=2)

        days_dim = hv.Dimension('Days')
        # convert to days
        t0 = trading_df.index[0]

        holding_df.index = ((holding_df.index - t0) / ONEDAY).astype(int)
        trading_df.index = ((trading_df.index - t0) / ONEDAY).astype(int)
        bitcoin_df.index = ((bitcoin_df.index - t0) / ONEDAY).astype(int)

        in_bitcoins_df.loc[:, 'holding'] += holding_df['BTC']
        in_bitcoins_df.loc[:, 'trading'] += trading_df['BTC']
        in_bitcoins_df.loc[:, 'bitcoin'] += bitcoin_df['BTC']
        in_usd_df.loc[:, 'holding'] += holding_df['USD']
        in_usd_df.loc[:, 'trading'] += trading_df['USD']
        in_usd_df.loc[:, 'bitcoin'] += bitcoin_df['USD']


    import pudb; pudb.set_trace()

    plot_opts = dict(line_width=2)
    my_object = hv.Curve((in_bitcoins_df.index, in_bitcoins_df['holding']), label='holding').opts(plot=plot_opts) * \
                hv.Curve((in_bitcoins_df.index, in_bitcoins_df['trading']), label='trading').opts(plot=plot_opts) * \
                hv.Curve((in_bitcoins_df.index, in_bitcoins_df['bitcoin']), label='bitcoin').opts(plot=plot_opts)

    _, temp = tempfile.mkstemp()
    renderer.save(my_object, temp, style=dict(Image={'cmap':'jet'}))

    """
    # upload html to s3
    s3_key = "{account}/plot.html".format(account=os.environ['BITTREX_ACCOUNT'])
    bucket = config.s3_client.Bucket(config.RESULTS_BUCKET)
    bucket.upload_file(temp, s3_key)
    """


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
            print time, m.time
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


def portfolio_change(current_portfolio):
    """
    Build and return a dataframe comparing change in portfolio holdings.
    
    :param current_portfolio: 
    :return: pd.DataFrame indexed by 'currency' with columns: '%', 'Diff', 'original', 'Current'
    """
    first_portfolio = portfolio.Portfolio.from_first_buy_order()

    original = first_portfolio.dataframe['Balance']
    current = current_portfolio.dataframe['Balance']
    difference = current - original
    percentage = difference * 100 / original

    change_df = pd.DataFrame({'Original': original,
                              'Current': current,
                              'Diff': difference,
                              '%': percentage})
    change_df.dropna(inplace=True)

    return change_df


if __name__ == "__main__":
    clean()
    recompute()
