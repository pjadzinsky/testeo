#!/usr/bin/python
import os


from portfolio import portfolio
import config
import report
import s3_utils


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

        os.environ['EXCHANGE_ACCOUNT'] = account
        print '*' * 80
        print 'EXCHANGE_ACCOUNT:', account

        current_portfolio = portfolio.Portfolio.from_bittrex()
        portfolio_change = report.portfolio_change(current_portfolio)
        print portfolio_change

        bitcoin_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/bitcoin.csv'.format(account=os.environ['EXCHANGE_ACCOUNT']))
        print '*' * 8
        print 'bitcoin_df'
        print bitcoin_df
        trading_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/trading.csv'.format(account=os.environ['EXCHANGE_ACCOUNT']))
        print '*' * 8
        print 'trading_df'
        print trading_df
        holding_df = s3_utils.get_df(config.RESULTS_BUCKET, '{account}/holding.csv'.format(account=os.environ['EXCHANGE_ACCOUNT']))
        print '*' * 8
        print 'holding_df'
        print holding_df

        holding_usd += holding_df['USD'].values[-1]
        trading_usd += trading_df['USD'].values[-1]
        bitcoin_usd += bitcoin_df['USD'].values[-1]
        holding_btc += holding_df['BTC'].values[-1]
        trading_btc += trading_df['BTC'].values[-1]
        bitcoin_btc += bitcoin_df['BTC'].values[-1]

    original_usd = 6000
    print 'holding_usd:', holding_usd
    print 'trading_usd:', trading_usd
    print 'bitcoin_usd:', bitcoin_usd
    print 'holding_btc:', holding_btc
    print 'trading_btc:', trading_btc
    print 'bitcoin_btc:', bitcoin_btc
    print '*' * 80
    print 'Ratio trading/holding (usd):', trading_usd / holding_usd
    print 'Ratio trading/bitcoin (usd):', trading_usd / bitcoin_usd
    print 'Ratio trading/original (usd):', trading_usd / original_usd


if __name__ == "__main__":
    main()


