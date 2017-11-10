#!/usr/bin/python
import os

from market import market
from portfolio import portfolio


def main(json_input, context):
    print '*' * 80
    print 'BITTREX_ACCOUNT:', os.environ['BITTREX_ACCOUNT']

    current_market = market.Market.from_bittrex()

    p = portfolio.Portfolio.last()
    p.report_value(current_market, 'trading.csv')




if __name__ == "__main__":
    main()
