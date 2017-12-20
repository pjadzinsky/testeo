#!/usr/bin/python

import report

def fix_buy_order_folder():
    """
    As of 2017/11/29 there is a bug in production and buy orders are logged into 'bittrex-buy-orders' rather than
    into 'bittrex-buy-orders/<account>'
    
    This has to be run until code is fixed an deployed to lambda
    
    I'm going to move them to the corresponding account. I'm counting on portfolios being different and some coins
     being only in one of them like for example:
    
    Pablo has: "EDG", XVG
    Gaby has: BAY, CLUB
     
    account: pablo should have  
    
    Last run: 2017/11/29
    """
    import config
    import s3_utils
    import os

    bucket = config.s3_client.Bucket(config.BUY_ORDERS_BUCKET)
    all_summaries = bucket.objects.all()
    for summary in all_summaries:
        if os.environ['BITTREX_ACCOUNT'] not in summary.key:
            index = s3_utils.get_df(config.BUY_ORDERS_BUCKET, summary.key, index_col=0).index
            if "EDG" in index and "BAY" not in index:
                print "aws s3 mv s3://{bucket}/{key} s3://{bucket}/pablo/{key} --profile=user2".format(
                    bucket=config.BUY_ORDERS_BUCKET, key=summary.key)
            elif "EDG" not in index and "BAY" in index:
                print "aws s3 mv s3://{bucket}/{key} s3://{bucket}/gaby/{key} --profile=user2".format(
                    bucket=config.BUY_ORDERS_BUCKET, key=summary.key)
            else:
                print "Error with key:", summary.key
                print "index:", index


def debug1():
    #report.plot()
    import state
    import time
    from portfolio import portfolio


    p = portfolio.Portfolio.from_bittrex()
    _, state1 = state.at_time(time.time())
    state2 =  state.from_portfolio(p)
    print '#' * 80
    print state1
    print state1.shape
    print '#' * 80
    print state2
    print state2.shape
    print '#' * 80
    #print state1.merge(state2, how='outer')
    print state.frames_are_equal(state1, state2)

def state_at_time():
    import time
    import state

    state.at_time(time.time())

def currency_changes_in_portfolio():
    import report
    report.currency_changes_in_portfolio()


def env_variables():
    import os
    print os.environ['PORTFOLIO_REPORT']
    print int(os.environ['PORTFOLIO_REPORT'])
    if int(os.environ['PORTFOLIO_REPORT']):
        print True
    else:
        print False


def bucket_timestamp():
    import s3_utils
    import config
    print s3_utils.bucket_timestamps(config.PORTFOLIOS_BUCKET)


def remove_equal():
    """
    I have a bunch of csvs in /tmp/<account>/<timestamp>.csv
    
    load them in order and for every pair, if 'first' == 'second' remove 'second'
    :return: 
    
    """
    import os
    import pandas as pd
    import numpy as np

    files = os.listdir('/tmp/pablo')
    files = ['/tmp/pablo/' + f for f in files]
    files.sort()

    first = files[0]
    df1 = pd.read_csv(first, index_col=0)
    for second in files[1:]:
        df2 = pd.read_csv(second, index_col=0)

        if len(df1)==len(df2) and np.all(df1.index == df2.index) and np.all(df1.Weight == df2.Weight):
            print 'removing', second
            os.unlink(second)
        else:
            print '\tkeeping', first
            df1 = df2


def report_change():
    import report
    from portfolio import portfolio
    current_portfolio = portfolio.Portfolio.from_bittrex()

    print report.portfolio_change(current_portfolio)

def plot():
    import report
    report.plot()


def fix_log_market():
    import log_markets
    import config
    from market import market
    import boto3
    s3 = boto3.resource('s3')

    bucket = config.s3_client.Bucket('my-bittrex')
    all_objects = bucket.objects.all()

    for object in all_objects:
        if 'prod' in object.key:
            continue

        if 'staging' in object.key:
            continue

        if 'short' not in object.key:
            continue

        import pudb; pudb.set_trace()
        current_market = market.Market.from_s3_key(object.key)
        log_markets._log_last_and_volume(current_market)

        copy_source = {
            'Bucket': 'my-bittrex',
            'Key': object.key
        }
        dest_key = 'prod/{}'.format(object.key)

        print copy_source
        print dest_key
        bucket.copy(copy_source, dest_key)

        new_object = s3.Object('my-bittrex', dest_key)
        msg = 'etags are equal: '
        if new_object.e_tag == object.e_tag:
            msg += 'True'
            print 'deleting:', object.key
            object.delete()
        else:
            msg += 'False'
        print msg



def fix_log_market2():
    import s3_utils
    import numpy as np

    df = s3_utils.get_df('my-bittrex', 'markets_lasts.csv')
    cols = df.drop('Unnamed: 0', axis=1).columns
    times = [int(c) for c in cols]
    diffs = np.diff(times)


if __name__ == "__main__":
    #bucket_timestamp()
    #currency_changes_in_portfolio()
    #remove_equal()
    #report_change()
    #plot()
    fix_log_market()
