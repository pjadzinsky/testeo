#!/usr/bin/python

from my_bittrex import volume
from my_bittrex.test import test_utils

# Start a portfolio from scratch, all positions are the same at start
def main():
    print 1
    portfolio = volume.Portfolio(target_portfolio_file='target_portfolio.csv', portfolio_file='test_portfolio.csv')
    portfolio.rebalance('BTC')

    #summaries = portfolio.market.get_summaries()
    #perturbed_summaries = test_utils.perturb_summary(summaries, 0.1)





if __name__ == "__main__":
    main()
