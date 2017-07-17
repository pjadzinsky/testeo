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


def fake_market(currency_prices_dict):
    """ Return a jsong blob as would be returned by bittrex.client.get_market_summaries
    but where the currencies and prices are the key/value pairs in currency_prices_dict
    """
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [
    """

    template = """
            "MarketName" : "{0}",
            "High" : {1},
            "Low" : {1},
            "Volume" : 10,
            "Last" : {1},
            "BaseVolume" : 1,
            "TimeStamp" : "2014-07-09T07:19:30.15",
            "Bid" : {1},
            "Ask" : {1},
            "OpenBuyOrders" : 15,
            "OpenSellOrders" : 15,
            "PrevDay" : {1},
            "Created" : "2014-03-20T06:00:00",
            "DisplayMarketName" : null
     """
    '''
    '''
    response += ','.join([template.format(k, v) for k, v in currency_prices_dict.iteritems()])
    response += ']}'


    response = response.replace('"Market', '{"Market')
    response = response.replace('null', 'null}')

    return response
