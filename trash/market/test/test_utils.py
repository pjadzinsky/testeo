import numpy as np

from trash.my_bittrex import volume


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


def fake_market(currency_prices_vols):
    """ Return a jsong blob as would be returned by bittrex.client.get_market_summaries
    but where the currencies, prices, volues are the tuples in currency_prices_vols
    """
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
    """

    template = """
            "MarketName" : "{0}",
            "High" : {1},
            "Low" : {1},
            "Volume" : {2},
            "Last" : {1},
            "BaseVolume" : {3},
            "TimeStamp" : "2014-07-09T07:19:30.15",
            "Bid" : {1},
            "Ask" : {1},
            "OpenBuyOrders" : 15,
            "OpenSellOrders" : 15,
            "PrevDay" : {1},
            "Created" : "2014-03-20T06:00:00",
            "DisplayMarketName" : null
     """
    response += '}, {'.join([template.format(c, b, v, v*b) for c, b, v in currency_prices_vols])
    response += '}]}'

    return response

def fake_currencies(currency_costs):
    """ 
    :param currency_costs: Each item is a tuple of the form (short-name, long-name, TxFee)
    :return: 
    """
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
    """

    template = """
               "Notice": null,
               "TxFee": {2},
               "CurrencyLong": "{1}",
               "CoinType": "BITCOIN",
               "Currency": "{0}",
               "MinConfirmation": 6,
               "BaseAddress": "LhyLNfBkoKshT7R8Pce6vkB9T2cP2o84hx",
               "IsActive": true
    """
    
    response += '}, {'.join([template.format(s, l, t) for s, l, t in currency_costs])
    response += '}]}'

    return response

def fake_balance(currencies_quantities):
    """
    Fake a balance. Each element in the list is a tuple of the form (currency, balance)
    """

    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
    """

    template = """
        "Currency" : "{0}",
        "Balance" : {1},
        "Available" : {1},
        "Pending" : 0.00000000,
        "CryptoAddress" : "DLxcEt3AatMyr2NTatzjsfHNoB9NT62HiF",
        "Requested" : false,
        "Uuid" : null
    """
    response += '}, {'.join([template.format(c, q) for c, q in currencies_quantities])
    response += '}]}'

    #response = response.replace('"Currency', '{"Currency')
    #response = respnose.replace('null', 'null}')
    return response
