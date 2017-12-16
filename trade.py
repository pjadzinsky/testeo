#!/usr/bin/python
import os

import bittrex_utils
from market import market
from portfolio import portfolio
import state
import report
print 'Finished with imports in', __file__


def main():
    print '*' * 80

    print 'BITTREX_ACCOUNT:', os.environ['BITTREX_ACCOUNT']
    print 'PORTFOLIO_SIMULATING:', os.environ['PORTFOLIO_SIMULATING']
    print 'PORTFOLIO_TRADE:', os.environ['PORTFOLIO_TRADE']
    print 'cancel all open orders'
    if os.environ['PORTFOLIO_TRADE'] == 'True':
        bittrex_utils.cancel_all_orders()

    # currently we have only XRP in bittrex, start a portfolio with 'desired' state given only by 'XRP' and 'ETH'
    currencies = os.environ['CURRENCIES'].split(',')
    desired_state = state.from_currencies(currencies)
    print '*'*80
    print 'Desired state:'
    print desired_state

    current_market = market.Market.from_bittrex()
    current_portfolio = portfolio.Portfolio.from_bittrex()
    print 'Current Portfolio'
    print current_portfolio.dataframe

    # log everything state, portfolio, values according to current market in BTC, USD (only logs if environmental
    # variable PORTFOLIO_REPORT is set
    report.during_trading(current_market, current_portfolio, desired_state)

    msg = current_portfolio.rebalance(current_market, desired_state, ['BTC'], 0, by_currency=False)
    print msg


def lambda_handler(event, context):
    print('Staring handler')
    print('event: {}'.format(event))
    print('context: {}'.format(context))
    main()


if __name__ == "__main__":
    main()
