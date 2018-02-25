#!/usr/bin/python2.7
""" Eithre trade or simulate a trade
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

print('Finished with imports in', __file__)


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

    currencies = os.environ['CURRENCIES'].split(',')
    desired_state = state.from_currencies(currencies)
    print('*'*80)
    print('Desired state:')
    print(desired_state)

    current_market = market.Market.from_exchange()
    current_portfolio = portfolio.Portfolio.from_exchange()
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
