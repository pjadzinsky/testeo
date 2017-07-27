#!/usr/bin/python
import os

from my_bittrex import volume

portfolio_csv = os.path.join('data', 'portfolio.csv')
market_csv = os.path.join('data', 'market.csv')


def main():
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'
    value = 10

    market = volume.Market()
    state = volume.define_state(market, 20, include_usd=True)
    base_currency = 'BTC'
    value = 10000

    portfolio = volume.Portfolio.from_csv()
    if portfolio is None:
        portfolio = volume.Portfolio()
        portfolio.start_portfolio(market, state, 'USDT', value)
        header = True
    else:
        header = False

    portfolio.ideal_rebalance(market, state)

    market.to_csv(header=header)
    portfolio.to_csv()


if __name__ == "__main__":
    main()
