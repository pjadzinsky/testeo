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

    import pudb; pudb.set_trace()

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


def env_variables():
    import os
    print os.environ['PORTFOLIO_REPORT']
    print int(os.environ['PORTFOLIO_REPORT'])
    if int(os.environ['PORTFOLIO_REPORT']):
        print True
    else:
        print False



if __name__ == "__main__":
    env_variables()