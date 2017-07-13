import numpy as np
import pandas as pd

def perturb_summary(summary, sigma):
    """
    Add some noise to the Last price of each MarketName in summary
    
    A market_name is a given currency trading for a different base currency ie, BTC-ETH
    
    :param summary: 
    :param sigma: contrast of gaussian noise to add
                a market_name trading at T will get noise from a gaussian distribution with std = T * sigma
                everyone gets noise from the same distribution for the time being
    :return: 
    """

    assert(type(summary), pd.DataFrame)
    sigmas = summary['Last'] * sigma
    perturbed = summary.copy()
    perturbed.loc[:, 'Last'] += np.random.randn(len(sigmas)) * sigmas
    return perturbed