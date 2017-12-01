#!/usr/bin/python
import os
import tempfile
from dateutil import parser

import pandas as pd

import bittrex_utils
import config
from market import market
from portfolio import portfolio
import state
import s3_utils

print 'Finished with imports in', __file__
if os.environ['LOGNAME'] == 'pablo':
    import holoviews as hv
    hv.extension('bokeh')



def report(current_market, current_portfolio, desired_state):

    current_portfolio.to_s3(current_market.time)
    state.save(current_market.time, desired_state)
    if os.environ['LOGNAME'] == 'pablo':
        portfolio_change(current_portfolio)
    deposits(current_market)
    trading_value(current_market, current_portfolio)
    bitcoin_value(current_market)
    holding_value(current_market)
    """
    plot()
    """


ONEDAY = 86400      # seconds in a day
def plot():
    renderer = hv.renderer('bokeh').instance(fig='html')

    holding_dfs = [s3_utils.get_df(config.RESULTS_BUCKET, '{account}/holding.csv'.format(account=account)) for
                   account in ['pablo', 'gaby']]
    trading_dfs = [s3_utils.get_df(config.RESULTS_BUCKET, '{account}/trading.csv'.format(account=account)) for
                   account in ['pablo', 'gaby']]
    bitcoin_dfs = [s3_utils.get_df(config.RESULTS_BUCKET, '{account}/bitcoin.csv'.format(account=account)) for
                   account in ['pablo', 'gaby']]

    holding_df = pd.concat(holding_dfs)
    trading_df = pd.concat(trading_dfs)
    bitcoin_df = pd.concat(bitcoin_dfs)

    # round time to day
    holding_df.loc[:, 'time'] == (holding_df['time'] // 86400) * 86400
    trading_df.loc[:, 'time'] == (trading_df['time'] // 86400) * 86400
    bitcoin_df.loc[:, 'time'] == (bitcoin_df['time'] // 86400) * 86400

    # group by 'time' and compute mean
    holding_df = holding_df.groupby('time', as_index=False).mean()
    trading_df = trading_df.groupby('time', as_index=False).mean()
    bitcoin_df = bitcoin_df.groupby('time', as_index=False).mean()

    """
    for account in ['pablo', 'gaby']:
        os.environ['BITTREX_ACCOUNT'] = account
        holding_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/holding.csv'.format(account=account))
        trading_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/trading.csv'.format(account=account))
        bitcoin_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/bitcoin.csv'.format(account=account))

        days_dim = hv.Dimension('Days')
        # convert to days
        t0 = trading_df.index[0]

        holding_df.index = ((holding_df.index - t0) / ONEDAY).astype(int)
        trading_df.index = ((trading_df.index - t0) / ONEDAY).astype(int)
        bitcoin_df.index = ((bitcoin_df.index - t0) / ONEDAY).astype(int)

    """
    plot_opts = dict(line_width=2, width=800)
    my_object = hv.Curve((holding_df['time'], holding_df['BTC']), label='holding.csv').opts(plot=plot_opts) * \
                hv.Curve((trading_df['time'], trading_df['BTC']), label='trading.csv').opts(plot=plot_opts) * \
                hv.Curve((bitcoin_df['time'], bitcoin_df['BTC']), label='bitcoin.csv').opts(plot=plot_opts)

    _, temp = tempfile.mkstemp()
    print temp
    renderer.save(my_object, temp, style=dict(Image={'cmap':'jet'}))

    """
    # upload html to s3
    s3_key = "{account}/plot.html".format(account=os.environ['BITTREX_ACCOUNT'])
    bucket = config.s3_client.Bucket(config.RESULTS_BUCKET)
    bucket.upload_file(temp, s3_key)
    """


def recompute():
    """
    Get all portfolios stored in PORTFOLIOS_BUCKET, and recompute csvs in RESULTS_BUCKET for each found portfolio
    
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
            print '*' * 80
            print 'processing portfolio from key:', summary.key
            p = portfolio.Portfolio.from_s3_key(summary.key)
            time = int(summary.key.rstrip('.csv').split('/')[-1])
            m = market.Market.at_time(time, 3600)

            desired_state = state.at_time(m.time)

            report(m, p, desired_state)



def clean():
    """
    Delete all files in RESULTS_BUCKET that contain the word os.environ['BITTREX_ACCOUNT'] in the key
    
    :return: 
        None
    """

    bucket = config.s3_client.Bucket(config.RESULTS_BUCKET)
    all_summaries = bucket.objects.all()
    objects = [{'Key': summary.key} for summary in all_summaries if os.environ['BITTREX_ACCOUNT'] in summary.key]
    if objects:
        bucket.delete_objects(Delete={'Objects': objects})




def deposits(market):
    """
    update <account>/deposits.csv, the csv will have columns time, BTC and USD with the deposits made since the
    last entry into this csv. If deposits are done in other currencies they are converted to BTC according to
    'market'
    
    :param market: 
    :return: 
    """
    account = os.environ['BITTREX_ACCOUNT']
    deposits_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/deposits.csv'.format(account=account))
    if deposits_df.empty:
        last_time = 0
    else:
        last_time = deposits_df['time'].iloc[-1]

    btc_value = 0
    for currency in ['BTC', 'ETH', 'XRP', 'LTC']:
        response = bittrex_utils.client.get_deposit_history(currency)
        for transaction_dict in response['result']:
            currency = transaction_dict['Currency']
            ammount = transaction_dict['Amount']
            time_str = transaction_dict['LastUpdated']
            datetime_obj = parser.parse(time_str)
            transaction_time = int(datetime_obj.strftime('%s'))

            if transaction_time > last_time and transaction_time < market.time:
                btc_value += market.currency_chain_value(['BTC', currency]) * ammount

        response = bittrex_utils.client.get_withdrawal_history(currency)
        print 'response:', response
        for transaction_dict in response['result']:
            currency = transaction_dict['Currency']
            ammount = transaction_dict['Amount']
            time_str = transaction_dict['Opened']
            datetime_obj = parser.parse(time_str)
            transaction_time = int(datetime_obj.strftime('%s'))
            if transaction_time > last_time and transaction_time < market.time:
                btc_value -= market.currency_chain_value(['BTC', currency]) * ammount

    if btc_value:
        usd_value = btc_value * market.currency_chain_value(['USDT', 'BTC'])
        s = pd.Series({'time': market.time, 'BTC': btc_value, 'USD': usd_value})
        updated = s3_utils.append_to_csv(s, config.RESULTS_BUCKET, '{account}/deposits.csv'.format(account=account))
    else:
        updated = deposits_df
    return updated


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

    account = os.environ['BITTREX_ACCOUNT']
    deposits_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/deposits.csv'.format(account=account))

    total_deposits = deposits_df.sum()
    total_bitcoin_deposits = total_deposits['BTC']
    total_usd_deposits = total_bitcoin_deposits * market.currency_chain_value(['USDT', 'BTC'])

    btc_value = pd.Series({'time': time, 'BTC': total_bitcoin_deposits, 'USD': total_usd_deposits})

    updated = s3_utils.append_to_csv(btc_value, config.RESULTS_BUCKET, '{account}/bitcoin.csv'.format(account=account))
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
    account = os.environ['BITTREX_ACCOUNT']

    try:
        portfolio_creation_time, _ = state.at_time(market.time)
        p = portfolio.Portfolio.at_time(portfolio_creation_time, 3600)
        btc_value = p.total_value(market, ['BTC'])
        usd_value = p.total_value(market, ['USDT', 'BTC'])

        s = pd.Series({'time': time, 'BTC': btc_value, 'USD': usd_value})
        updated = s3_utils.append_to_csv(s, config.RESULTS_BUCKET, '{account}/holding.csv'.format(account=account))
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
    account = os.environ['BITTREX_ACCOUNT']

    btc_value = current_portfolio.total_value(market, ['BTC'])
    usd_value = current_portfolio.total_value(market, ['USDT', 'BTC'])

    s = pd.Series({'time': time, 'BTC': btc_value, 'USD': usd_value})
    updated = s3_utils.append_to_csv(s, config.RESULTS_BUCKET, '{account}/trading.csv'.format(account=account))
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
    #clean()
    recompute()
