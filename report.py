#!/usr/bin/python
import os
import tempfile

import pandas as pd

import bittrex_utils
import config
from market import market
from portfolio import portfolio
import utils


def main(json_input, context):
    print '*' * 80
    print 'BITTREX_ACCOUNT:', os.environ['BITTREX_ACCOUNT']

    current_market = market.Market.from_bittrex()

    p = portfolio.Portfolio.last()
    p.report_value(current_market, 'trading.csv')

    total_bitcoin = total_bitcoin_deposit()
    s = pd.Series({'time': current_market.time, 'BTC': total_bitcoin})
    utils.update_csv(s, config.RESULTS_BUCKET, 'bitcoins.csv')

    total_usd = total_USD_deposit(current_market)
    s = pd.Series({'time': current_market.time, 'USD': total_usd})
    utils.update_csv(s, config.RESULTS_BUCKET, 'usd.csv')


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
    row = df[df['time']==market.time].index[0]

    if row == 0:
        bitcoins_added = df.loc[0, 'BTC']
    else:
        bitcoins_added = df.loc[row, 'BTC'] - df.loc[row - 1, 'BTC']

    usd = bitcoins_added * market.currency_chain_value(['USDT', 'BTC'])
    return usd




if __name__ == "__main__":
    main(None, None)
