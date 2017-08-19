#!/usr/bin/python
import time

from markets import recreate_markets, market_operations


def main():
    # 'state' is the desired composition of our portfolio. When we 'rebalance' positions we do it
    # to keep rations between different currencies matching those of 'state'
    df = recreate_markets.get_markets()

    print df.shape
    print df.head()
    df = df.loc[(1502981286, slice(None)), :]
    df.index = df.index.droplevel()
    print df.head()
    t0 = time.time()
    first_market = recreate_markets.first_market()
    t1 = time.time() - 12 * 3600
    recreate_markets.closest_market(t1)
    market_volumes = market_operations.usd_volumes(first_market)
    print market_volumes
    t2 = time.time()


    """
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

    print "Market value:", portfolio.total_value(market, ['BTC', 'USDT'])
    """


if __name__ == "__main__":
    main()
