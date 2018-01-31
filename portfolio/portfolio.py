"""
bittrex.client returns balances as a list of dictionaries with:
 Currency, Available, Balance, CryptoAddress, Pending, Requested, Uuid

A portfolio is the type and amount of each cryptocurrency held along with some basic operations.
.
There is a desired 'state' and due to fluctuations some currencies will have more (or less) total_value than their
desired target 'state'. We'll rebalance them periodically.
To avoid spending too much in commissions when rebalancing we have a 'threshold' and we only 'rebalance
cryptocurrencies that increased (or decreased) more than 'threshold' (as a percentage) from desired 'state'.
For example is the desired state is 100 and the threshold is 0.1 we'll sell only if the current total_value is at or above
110 (and buy if the current total_value is at or below 90)
To prevent from buying too much of a sinking currency we are going to put bounds on either the price and/or the
quantities (not clear yet). One idea is to compute the ratio between the current balance and the initial balance
per currency and then say that no currency can have a ratio that is N times bigger than the average ratio.
"""
print 'About to start loading modules from', __file__
import os
import tempfile

import numpy as np
import pandas as pd


from exchanges.exchange import exchange
import config
import s3_utils
import state
print 'Finished with imports in', __file__

COMMISION = 0.25/100
SATOSHI = 10**-8  # in BTC
MINIMUM_TRADE = 100000   # in SAT (satohis)

class Portfolio(object):
    def __init__(self, dataframe):
        """
        Read portfolio from API
        """
        self.dataframe = dataframe

    @classmethod
    def from_state(cls, market, state, base, value):
        p = cls._start_portfolio(market, state, base, value)
        return p

    @classmethod
    def from_simulation_index(cls, sim_index):
        params_df = pd.read_csv(config.PARAMS, index_col=0)
        sim_params = params_df.loc[sim_index]
        p = cls.from_simulation_params(0, sim_params)
        return p

    @classmethod
    def from_simulation_params(cls, market, sim_params):
        base = sim_params['base']
        value = sim_params['value']

        state = sim_params.to_frame()
        for key in config.PARAMS_INDEX_THAT_ARE_NOT_CURRENCIES:
            if key in state.index:
                state.drop(key, inplace=True, axis=0)
        state.columns = ['Weight']
        p = cls._start_portfolio(market, state, base, value)
        return p

    @classmethod
    def from_exchange(cls):
        return cls(exchange.get_balances().to_frame())

    @classmethod
    def from_first_buy_order(cls):
        """ return the portfolio first traded after the 'state' was last updated.
        
        (We are actually trying to load the portfolio from the first 'buy' order, some currencies might not have been
        executed at the requested limit buy/sell)
        
        In case the Buy order does not exist, try to load the portfolio from config.PORTFOLIOS_BUCKET
        """
        orders_bucket = config.s3_client.Bucket(config.BUY_ORDERS_BUCKET)

        # get the timestamp corresponding to the 'state' definiition.
        # IF there is a csv in bittrex-buy-orders bucket matching <account>/<time_stamp>_buy_df.csv. Load
        # portfolio from this key
        time_stamp, _ = state.current()
        all_summaries = orders_bucket.objects.all()
        for summary in all_summaries:
            if str(time_stamp) in summary.key:
                buy_order_df = s3_utils.get_df(orders_bucket.name, summary.key, comment='#', index_col=0)
                buy_order_df.loc[:, 'Available'] = buy_order_df['target_currency']
                buy_order_df.loc[:, 'Balance'] = buy_order_df['target_currency']
                buy_order_df = buy_order_df[buy_order_df['Available'] > 0]

                return cls(buy_order_df[['Available', 'Balance', 'Pending']])

        # if we get here, is because '<account>/<time_stamp>_buy_df.csv' was not found in BUY_ORDERS_BUCKET
        # In this case, we'll use the 1st portfolio defined after time_stamp (when the 'state' was defined)
        portfolios_bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)
        all_summaries = portfolios_bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])
        time_diff = np.inf
        key = None
        for summary in all_summaries:
            # summary.key is of the form <account>/<time_stamp>.csv
            portfolio_time = int(summary.key.rstrip('.csv').split('/')[1])
            if portfolio_time > time_stamp and portfolio_time - time_stamp < time_diff:
                time_diff = portfolio_time - time_stamp
                key = summary.key
        if key:
            return cls.from_s3_key(summary.key)
        else:
            return None

    @classmethod
    def from_csv(cls, csv):
        dataframe = pd.read_csv(csv, index_col=0)
        return cls(0, dataframe)

    @classmethod
    def from_s3_key(cls, s3_key):
        _, temp = tempfile.mkstemp()
        config.s3_client.Bucket(config.PORTFOLIOS_BUCKET).download_file(s3_key, temp)
        dataframe = pd.read_csv(temp, index_col=0, comment='#')
        return cls(dataframe)

    @classmethod
    def at_time(cls, timestamp, max_time_difference):
        bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)
        for summary in bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT']):
            time = int(summary.key.split('/')[-1].rstrip('.csv'))
            if abs(time - timestamp) < max_time_difference:
                return cls.from_s3_key(summary.key)

    @classmethod
    def after_time(cls, timestamp):
        max_time_difference = np.inf
        best_key = None
        bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)
        for summary in bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT']):
            time = int(summary.key.split('/')[-1].rstrip('.csv'))
            if time >= timestamp and  time - timestamp < max_time_difference:
                max_time_difference = time - timestamp
                best_key = summary.key

        if best_key:
            return cls.from_s3_key(best_key)

    @classmethod
    def before_time(cls, timestamp):
        max_time_difference = np.inf
        best_key = None
        bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)
        for summary in bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT']):
            time = int(summary.key.split('/')[-1].rstrip('.csv'))
            if time <= timestamp and  timestamp - time < max_time_difference:
                max_time_difference = timestamp - time
                best_key = summary.key

        if best_key:
            return cls.from_s3_key(best_key)

    @classmethod
    def last_logged(cls):
        bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)

        all_object_summaries = bucket.objects.filter(Prefix=os.environ['EXCHANGE_ACCOUNT'])
        all_keys = [aos.key for aos in all_object_summaries]

        # each key is of the form <account>/timestamp.csv. Keep only timestamp and convert it to an int
        timestamps = [int(key.rstrip('.csv').split('/')[1]) for key in all_keys]

        # find the key corresponding to the last timestamp
        last_index = np.argmax(timestamps)
        last_key = all_keys[last_index]

        return cls.from_s3_key(last_key)


    def copy(self):
        cls = self.__class__
        new_df = self.dataframe.copy()
        return cls(new_df)


    @staticmethod
    def _start_portfolio(market, state, base, value):
        """
        We first start a portfolio that has just 'value' in 'base' and then execute ideal_rebalance on it
        :param market: 
        :param state: 
        :param base: 
        :param value: 
        :return: 
        """
        intermediate_currencies = ['BTC']
        dataframe = pd.DataFrame({'Balance': value, 'Available': value, 'Pending': 0}, index=[base])
        portfolio = Portfolio(dataframe=dataframe)

        portfolio.rebalance(market, state, intermediate_currencies, 0)

        return portfolio

    def total_value(self, market, intermediate_currencies):
        """
        Compute the total amount of the portfolio
        param: intermediate_currendcies: list of str
            for each currency in self.dataframe.index 
            intermdiate_currencies + [currency] has to be a valid currency chain
            [A, B, C] (c trades with B and B trades with A and A is the base price to return in)
        """
        return self.value_per_currency(market, intermediate_currencies).sum()

    def value_per_currency(self, market, intermediate_currencies):
        portfolio = self.dataframe

        return portfolio.apply(lambda x: market.currency_chain_value(intermediate_currencies + [x.name]) * x['Available'],
                               axis=1)
    def ideal_rebalance(self, market, state, intermediate_currencies):
        """
        Given market, state and intermediate_currencies return the amount to buy (+) or sell (-) for each currency
        to achieve perfect balance.
        
        At this point we don't look at trading costs, sinking currencies, etc
        
        returned dataframe has columns:
        target_base:    the value in 'base' we should have in each currency after rebalancing
        target_currency:    the ideal amount of each currency that achieves this ideal rebalancing
        Buy:            the amount of currency that we have to buy (if > 0) or sell (if < 0) to obtain
                        target_currency
        Buy (base):     Amount of base needed for the transaction (not taking transactions costs into account)
        intermediate_currencies:    each currency in 'state' will be converted to values in 'base' where base is
                                    intermediate_currencies[0] and the conversion is done by traversing
                                    from currency in state to intermediate_currencies[-1], then to
                                    intermediate_currencies[-2], ..., ending in intermediate_currencies[0]
                                    
                                    most likely this is going to be either:
                                        ['USDT', 'BTC']
                                        ['USDT', 'ETH']
                                        ['BTC']
                                        ['ETH']
        """
        total_value = self.total_value(market, intermediate_currencies)

        buy_df = pd.merge(self.dataframe, state, left_index=True, right_index=True, how='outer')      # if state has new cryptocurrencies there will be NaNs
        buy_df.fillna(0, inplace=True)

        base = intermediate_currencies[0]

        buy_df.loc[:, 'target_base'] = buy_df['Weight'] * total_value
        buy_df.loc[:, 'currency_in_base'] = buy_df.apply(
            lambda x: market.currency_chain_value([base] + intermediate_currencies + [x.name]), axis=1)
        buy_df.loc[:, 'target_currency'] = buy_df['target_base'] / buy_df['currency_in_base']

        buy_df.loc[:, 'Buy'] = buy_df['target_currency'] - buy_df['Available']
        buy_df.loc[:, 'Buy ({base})'.format(base=intermediate_currencies[0])] = buy_df.apply(
            lambda x: x.Buy * market.currency_chain_value([base] + intermediate_currencies + [x.name]),
            axis=1
        )

        return buy_df

    def rebalance(self, market, state, intermediate_currencies, min_percentage_change=0, by_currency=False):
        """
        Given a state, buy/sell positions to approximate target_portfolio
        
        base_currency:  base currency to do computations
        min_percentage_change:  currencies are only balanced if difference with target is above/below this threshold
                                (express as a percentage)
        by_currency:    bool, when computing percentage_change we can do so by currency or in intermediate_currencies[0]
        """
        buy_df = self.ideal_rebalance(market, state, intermediate_currencies)
        if os.environ['PORTFOLIO_SIMULATING'] == 'True':
            # apply transaction costs
            buy_df.loc[:, 'Buy'] = buy_df['Buy'].apply(apply_transaction_cost)

        base = intermediate_currencies[0]

        # we only buy/sell if movement is above 'min_percentage_change'. However, this movement could be in the
        # amount of cryptocurrency we own (by_currency=True) or in the amount of 'base' it represents (by_currency=False)
        if min_percentage_change > 0:
            for currency in buy_df.index:
                if by_currency:
                    # if 'buy_df['Buy'] represents less than 'min_percentage_change' from 'position' don't do anything
                    percentage_change = np.abs(buy_df.loc[currency, 'Buy']) / buy_df.loc[currency, 'Balance']
                else:
                    # if 'buy_df['Buy (base)'] represents less than 'min_percentage_change' from 'position' don't do anything
                    percentage_change = np.abs(buy_df.loc[currency, 'Buy ({})'.format(base)]) / \
                                        buy_df.loc[currency, 'target_base']
                buy_df.loc[currency, "change"] = percentage_change
                if percentage_change < min_percentage_change:
                    buy_df.loc[currency, 'Buy'] = 0

        # if 'base' is in self.dataframe, remove it. Each transaction is done/simulated against 'base'. We don't
        # buy/sell 'base' directly. Not doing this will lead to problems and double counting
        if base in buy_df.index:
            remove_transaction(buy_df, base)

        # As of 01/28/2017 this was 100K Satoshi's for Bittrex
        apply_min_transaction_size(market, buy_df, base)

        msg = ''
        if os.environ['PORTFOLIO_SIMULATING'] == 'True':
            self.mock_buy(buy_df[['Buy', 'Buy ({})'.format(base), 'change']])
        else:
            self.buy(market, buy_df, base)


    def mock_buy(self, buy_df):
        """
        This is a method that mocks sending a buy/sell order to the client and its execution.
        After this method executes, we'll assume that we buy/sell whatever we requested at the requested prices
        
        I don't understand if bittrex client talks in usdt, base or currency when placing orders. I'm just
        mocking the result here, not the call
        
        :param buy_df: 
        :return: 
        """

        # There is 0.25% cost on each buy/sell transaction. Although exchanging ETH for BTC shows as two transactions
        # in 'buy' and should pay 0.25% only once, most transactions in 'buy' should pay the 0.25%. I'm going to
        # overestimate the transaction cost by paying the 0.25% for every transaction in buy
        # when we want to buy X, we end up with x * (1 - cost)
        # when we want to sell X, we end up with x * (1 - cost) base. I'm modeling this as we actuall sold
        # x * (1 + cost)

        # get 'base' name from the column named 'Buy (base)'
        column = [c for c in buy_df.columns if c.startswith("Buy (")][0]
        base = column[5:-1]

        # the 'index' in buy_df might not be the same as in self.dataframe. That's why we start merging based on
        # index and we use 'outer'.
        self.dataframe = pd.merge(self.dataframe, buy_df, left_index=True, right_index=True, how='outer')
        #  If new values are added to index there will be NaN
        self.dataframe.fillna(0, inplace=True)
        self.dataframe['Balance'] += self.dataframe['Buy']
        self.dataframe['Available'] += self.dataframe['Buy']

        self.dataframe.loc[base, 'Balance'] -= self.dataframe[column].sum()
        self.dataframe.loc[base, 'Available'] -= self.dataframe[column].sum()
        self.dataframe.drop(['Buy', column, 'change'], inplace=True, axis=1)

    def buy(self, market, buy_df, base_currency):
        """
        Send buy/sell requests for all rows in buy_df
        
        :param buy_df: 
        :param base_currency: 
        :return: 
        """
        import pudb; pudb.set_trace()

        for currency, row in buy_df.iterrows():
            market_name = _market_name(base_currency, currency)
            amount_to_buy_in_base = row['Buy ({})'.format(base_currency)]
            amount_to_buy_in_currency = row['Buy']
            if amount_to_buy_in_currency == 0:
                continue
            rate = amount_to_buy_in_base / amount_to_buy_in_currency
            satoshis = row['SAT']

            if amount_to_buy_in_base > 0:
                msg_order = 'send BUY order'
                trade = exchange.buy_limit
            else:
                msg_order = 'send SELL order'
                trade = exchange.sell_limit
                amount_to_buy_in_currency *= -1

            print '*' * 80
            # Do not change next next condition. The environmental variable is a string, not a bool
            if not os.environ['PORTFOLIO_TRADE'] == 'True':
                print "PORTFOLIO_TRADE: False\n"
            print msg_order
            print 'Market_name: {}, amount: {}, rate: {} ({} SAT)\n'.format(market_name, amount_to_buy_in_currency,
                                                                           rate, satoshis)

            if os.environ['PORTFOLIO_TRADE'] == 'True':
                trade(market_name, amount_to_buy_in_currency, rate)

                # log the requested portfolio
                s3_key = '{account}/{time}_buy_df.csv'.format(account=os.environ['EXCHANGE_ACCOUNT'],
                                                              time=int(market.time))
                s3_utils.log_df(config.BUY_ORDERS_BUCKET, s3_key, buy_df)


    def limit_to(self, limit_df):
        """
        limit self.dataframe to the given limit_df
        If a currency is in both self.dataframe and limit_df, the 'Available' and 'Balance' fields
        of self.dataframe are updated to the minimum between self.dataframe['Available'] and limit_df['Limit']
        
        for example if self.dataframe looks like:
                Available   Balance Pending CryptoAddress
        BTC       2.3            2.3     0       xxx
        ETH      53.1           53.1     0       yyy
        XRP    1200.0         1200.0     0       zzz
        
        and limit_df is:
                Limit
        BTC      1.2
        XRP     600
        
        Then self.dataframe becomes
                Available   Balance Pending CryptoAddress
        BTC        1.2           1.2     0       xxx
        ETH      53.1           53.1     0       yyy
        XRP     600.0          600.0     0       zzz
        
        
        :param currencies_df: 
        :return:    None, operates in self.dataframe in place 
        """
        for currency, limit in limit_df.iteritems():
            if currency in self.dataframe.index:
                new_value = min(self.dataframe.loc[currency, 'Available'], limit)
                if new_value == 0:
                    print 'Removing {} from portfolio'.format(currency)
                    self.dataframe.drop(currency, inplace=True)
                else:
                    print 'new limit for {} is {}'.format(currency, new_value)
                    self.dataframe.loc[currency, 'Available'] = new_value
                    self.dataframe.loc[currency, 'Balance'] = new_value


    def to_s3(self, time_sec):
        """ Store self.dataframe in the given key
        """
        if os.environ['PORTFOLIO_REPORT'] == 'True':
            assert self.dataframe.index.name == 'Currency'
            bucket = config.s3_client.Bucket(config.PORTFOLIOS_BUCKET)
            s3_key = '{account}/{time}.csv'.format(account=os.environ['EXCHANGE_ACCOUNT'],
                                                   time=time_sec)
            _, temp = tempfile.mkstemp()
            self.dataframe.to_csv(temp)
            bucket.upload_file(temp, s3_key)


def remove_transaction(buy_df, currency):
    columns = [c for c in buy_df.columns if c.startswith('Buy')]
    buy_df.loc[currency, columns] = 0


def apply_min_transaction_size(market, buy_df, base):
    """ Minimum transaction size is 50K Satoshis or 0.0005 BTC"""
    # add a column to buy_df that is the amount of the transaction in SATOSHI
    column = 'Buy ({base})'.format(base=base)
    buy_df.loc[:, 'SAT'] = buy_df[column] * market.currency_chain_value(['BTC', base]) / SATOSHI

    below_min_transaction = np.abs(buy_df['SAT']) < MINIMUM_TRADE

    for currency, remove_flag in below_min_transaction.iteritems():
        if remove_flag:
            satoshis = buy_df.loc[currency, 'SAT']
            print "Removing {} from transactions. Amount in satoshis is {}".format(currency, satoshis)
            remove_transaction(buy_df, currency)


def _market_name(base, currency):
    name = base + '-' + currency

    if name in exchange.market_names():
        return name

    return None


def apply_transaction_cost(buy):
    """ buy is a float, the amount of either currency or dollars to buy (if positive) or sell (if negative)
    """
    try:
        buy *= 1.0
    except:
        raise IOError('buy should be numeric')

    if buy > 0:
        buy -= buy * COMMISION
    else:
        buy += buy * COMMISION

    return buy


print 'finished loading', __file__
