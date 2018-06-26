#!/usr/bin/python2.7
""" Either trade or simulate a trade
This script requires environmental variables:
    PORTFOLIO_SIMULATING:   'True' or 'False'
    PORTFOLIO_TRADE:    'True' or 'False'   (these two are redundant are to make sure we don't pass the wrong logic
                                            before there is a typo in a string like 'false' instead of 'False'
    PORTFOLIO_REPORT:   'True' or 'False'   (if True many computations and intermediate results are logged to s3
    CURRENCIES: comma separated list of currencies that make the portfolio
    EXCHANGE: POLONIEX or BITTREX for the time being
    EXCHANGE_ACCOUNT:   String to identify account within an exchange. Only used in logging and grabing data from s3
                        has nothing to do with operating since that is determined by the <EXCHANGE>_KEY/SECRET
    LOGNAME:    aws or pablo, in aws we use default profile, in my laptop I use a different one
    <EXCHANGE>_ENCRYPTED_KEY:   str to talk to API
    <EXCHANGE>_ENCRYPTED_SECRET: str to talk to API
    
    
 """
import os

import report
import state
from exchanges import exchange
from portfolio import portfolio
import market

if os.environ['LOGNAME'] == 'aws':
    print('Finished loading', __file__)


BITTREX_EXCLUDE_COINS = ['BTCP', 'EDG', 'SYS', 'TRIG', 'USDT']
POLONIEX_EXCLUDE_COINS = ['BCH', 'USDT', 'GAS']
POLONIEX_PRIVATE_COINS = {'BTC': 0.10972517 + 0.00091267}   # total 0.11063784, buy 60 @ .0018353
BITTREX_PRIVATE_COINS = {'BTC': 0.0}

def main():
    print('*' * 80)
    print('PORTFOLIO_SIMULATING:', os.environ['PORTFOLIO_SIMULATING'])
    print('PORTFOLIO_TRADE:', os.environ['PORTFOLIO_TRADE'])
    print('cancel all open orders')

    if os.environ['PORTFOLIO_TRADE'] == 'True':
        #pass
        exchange.cancel_all_orders()
    else:
        print('Would be canceling all orders from {}'.format(os.environ['EXCHANGE']))
    __import__('pudb').set_trace()

    currencies = os.environ['CURRENCIES'].split(',')
    desired_state = state.from_currencies(currencies)
    print('*'*80)
    print('Desired state:')
    print(desired_state)

    current_market = market.Market.from_exchange()
    current_portfolio = portfolio.Portfolio.from_exchange()

    # exclude some currencies from portolio, edited as needed
    if os.environ['EXCHANGE'] == 'BITTREX':
        exclude_coins = BITTREX_EXCLUDE_COINS
        private_coins = BITTREX_PRIVATE_COINS
    elif os.environ['EXCHANGE'] == 'POLONIEX':
        exclude_coins = POLONIEX_EXCLUDE_COINS
        private_coins = POLONIEX_PRIVATE_COINS
    else:
        exclude_coins = []

    for coin in exclude_coins:
        if coin in current_portfolio.values:
            current_portfolio.values.drop(coin, inplace=True)
        if coin in desired_state.index:
            desired_state.drop(coin, inplace=True)

    # limit currencies to some of all the available
    for private_coin, private_value in private_coins.items():
        if private_coin in current_portfolio.values:
            current_portfolio.values[private_coin] -= private_value

    print('Current Portfolio')
    print(current_portfolio.values)

    # log everything state, portfolio, values according to current market in BTC, USD (only logs if environmental
    # variable PORTFOLIO_REPORT is set
    #report.during_trading(current_market, current_portfolio, desired_state)

    current_portfolio.rebalance(current_market, desired_state, ['BTC'], 0, by_currency=False)


def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


if __name__ == "__main__":
    main()
