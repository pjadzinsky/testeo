#!/usr/bin/python
import os
import time

import pandas as pd

import config
import s3_utils
import state
from exchanges import exchange
from portfolio import portfolio
import market

print 'Finished with imports in', __file__
if os.environ['LOGNAME'] == 'pablo':
    import holoviews as hv
    hv.extension('bokeh')



def during_trading(current_market, current_portfolio, desired_state):

    current_portfolio.to_s3(current_market.time)
    state.save(current_market.time, desired_state)
    #deposits(current_market)
    trading_value(current_market, current_portfolio)
    #bitcoin_value(current_market)
    #holding_value(current_market)


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

    # group by 'time' and compute totals
    holding_df = holding_df.groupby('time', as_index=False).sum()
    trading_df = trading_df.groupby('time', as_index=False).sum()
    bitcoin_df = bitcoin_df.groupby('time', as_index=False).sum()

    """
    for account in ['pablo', 'gaby']:
        os.environ['EXCHANGE_ACCOUNT'] = account
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

    #if os.path.isfile('/tmp/trading_btc.html')
    temp = '/tmp/trading_btc'
    #_, temp = tempfile.mkstemp()
    #print temp
    renderer.save(my_object, temp, style=dict(Image={'cmap':'jet'}))

    """
    # upload html to s3
    s3_key = "{account}/plot.html".format(account=os.environ['EXCHANGE_ACCOUNT'])
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
    all_summaries = bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])
    for summary in all_summaries:
        print '*' * 80
        print 'processing portfolio from key:', summary.key
        p = portfolio.Portfolio.from_s3_key(summary.key)
        time = int(summary.key.rstrip('.csv').split('/')[-1])
        m = market.Market.at_time(time, 3600)

        desired_state = state.at_time(m.time)

        report(m, p, desired_state)



def clean():
    """
    Delete all files in RESULTS_BUCKET that contain the word os.environ['EXCHANGE_ACCOUNT'] in the key
    
    :return: 
        None
    """

    bucket = config.s3_client.Bucket(config.RESULTS_BUCKET)
    all_summaries = bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])
    objects = [{'Key': summary.key} for summary in all_summaries]
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
    account = os.environ['EXCHANGE_ACCOUNT']
    deposits_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/deposits.csv'.format(account=account))
    if deposits_df.empty:
        last_time = 0
    else:
        last_time = deposits_df['time'].iloc[-1]

    df = exchange.withdrawals_and_deposits()
    df = df[(df['TimeStamp'] > last_time) & (df['TimeStamp'] < market.time)]

    def in_btc(row):
        if row['Type'] == 'deposit':
            sign = 1
        elif row['Type'] == 'withdrawal':
            sign = -1
        else:
            raise IOError

        amount = row['Amount'] * market.currency_chain_value(['BTC'], row['Currency']) * sign
        return amount

    df.loc[:, 'btc_value'] = df.apply(lambda row: in_btc(row), axis=1)

    btc_value = df['btc_value'].sum()

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

    account = os.environ['EXCHANGE_ACCOUNT']
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
    account = os.environ['EXCHANGE_ACCOUNT']

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
    account = os.environ['EXCHANGE_ACCOUNT']

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

    state_timestamp, _ = state.at_time(time.time())
    first_portfolio = portfolio.Portfolio.after_time(state_timestamp)

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


def currency_changes_in_portfolio():
    """ Load all the portfolios in config.PORTFOLIOS_BUCKET/<account>/<time>.csv
    and every time there is a chnage in the currencies, print the timestamp of the new portfolio, and the change
    in currencies
    """
    bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)

    previous_currencies = set([])
    all_summaries = bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])
    try:
        os.makedirs('/tmp/{}'.format(os.environ['EXCHANGE_ACCOUNT']))
    except:
        pass
    for summary in all_summaries:
        df = s3_utils.get_df(config.PORTFOLIOS_BUCKET, summary.key, index_col=0)
        df = df[df['Balance']>0]
        current_currencies = set(df.index.tolist())

        time = int(summary.key.split('/')[1].replace('.csv', ''))
        if previous_currencies != current_currencies:
            print '*' * 80
            print 'Time:', time
            print 'Currencies gone:', previous_currencies.difference(current_currencies)
            print 'New currencies:', current_currencies.difference(previous_currencies)
            print 'len(new_currencies) =', len(current_currencies)
            if len(current_currencies) % 2 and 'BTC' in current_currencies:
                current_currencies.discard('BTC')

            if len(current_currencies) == 0:
                continue

            df = state.from_currencies(current_currencies)
            df.to_csv('/tmp/{account}/{time}.csv'.format(account=os.environ['EXCHANGE_ACCOUNT'],
                                                    time=time))
            print 'All currencies:', current_currencies
            previous_currencies = current_currencies

        print summary.key


if __name__ == "__main__":
    #clean()
    recompute()
