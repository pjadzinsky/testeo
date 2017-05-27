import deribit_api
import GDAX

#last_derivit = deribit_api.index()['btc']

gdax_client = GDAX.PublicClient()
deribit_client = deribit_api.RestClient()


def gdax_variation():
    stats = gdax_client.getProduct24HrStats('btc')
    return float(stats['last'])/float(stats['high'])


def deribit_variation():
    stats = deribit_client.index()['btc']
    return stats
