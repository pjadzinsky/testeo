#!/usr/bin/python
import os

import report
import state
from exchanges.exchange import exchange
from portfolio import portfolio
import market

print 'Finished with imports in', __file__


def main():
    print '*' * 80

    print 'PORTFOLIO_SIMULATING:', os.environ['PORTFOLIO_SIMULATING']
    print 'PORTFOLIO_TRADE:', os.environ['PORTFOLIO_TRADE']
    print 'cancel all open orders'
    if os.environ['PORTFOLIO_TRADE'] == 'True':
        exchange.cancel_all_orders()

    # currently we have only XRP in bittrex, start a portfolio with 'desired' state given only by 'XRP' and 'ETH'
    currencies = os.environ['CURRENCIES'].split(',')
    desired_state = state.from_currencies(currencies)
    print '*'*80
    print 'Desired state:'
    print desired_state

    current_market = market.Market.from_exchange()
    current_portfolio = portfolio.Portfolio.from_exchange()
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
