import numpy as np
import pandas as pd

from my_bittrex import volume

def perturb_market(market, sigma):
    """
    Add some noise to the Last price of each MarketName in summary
    
    A market_name is a given currency trading for a different base currency ie, BTC-ETH
    
    :param summary: 
    :param sigma: contrast of gaussian noise to add
                a market_name trading at T will get noise from a gaussian distribution with std = T * sigma
                everyone gets noise from the same distribution for the time being
    :return: 
    """

    assert(type(market), volume.Market)
    sigmas = market.summaries()['Last'] * sigma
    market._summaries.loc[:, 'Last'] += np.random.randn(len(sigmas)) * sigmas
