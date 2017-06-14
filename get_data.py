import time

import deribit_api
import GDAX
from exchanges import bitstamp
from exchanges import gemini
from exchanges import deribit
from exchanges import kraken
try:
    import ccs
    print 'ccs is working'
except:
    print 'ccs does not work'

#last_derivit = deribit_api.index()['btc']

deribit_client = deribit_api.RestClient()
gdax_public_client = GDAX.PublicClient()


def last():
    """ Get the last transaction in each exchange
    """
    output = {}
    output['bitstamp'] = bitstamp.ticker('btcusd')['last']
    output['gemini'] = gemini.ticker('btcusd')['last']
    output['GDAX'] = gdax_public_client.getProductTicker()['price']
    output['deribit'] = deribit_client.index()['btc']
    output['kraken'] = kraken.ticker('XXBTZUSD')['XXBTZUSD']['c'][0]

    return output


def get_time():
    return int(time.time())


def order_book():
    symbol = 'BTC-USD'
    return gdax_public_client.getProductOrderBook(product=symbol, level=2)


