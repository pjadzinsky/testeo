from decimal import Decimal
import get_data


def add_data(table):
    """ Add several values to a row in the table.
    
    Values to add are:
        last ticker in several exchanges like bitstamp, GDAX, gemini, kraken, deribit

        order book (from GDAX)

        time (epoch seconds)
    """

    output = get_data.last()
    output['time'] = get_data.get_time()
    ob = get_data.order_book()
    output['bids'] = ob['bids']
    output['asks'] = ob['asks']

    response = table.put_item(Item={
        'symbol': 'BTC-USD',
        'time': int(output['time']),
        'bids': output['bids'],
        'asks': output['asks'],
        'bitstamp': Decimal(output['bitstamp']),
        'GDAX': Decimal(output['GDAX']),
        'kraken': Decimal(output['kraken']),
        'gemini': Decimal(output['gemini'])
    })

    return response
"""
def get_data():

    client = GDAX.PublicClient()
    order_book = client.getProductOrderBook(product=SYMBOL, level=2)
    ticker = client.getProductTicker(SYMBOL)
    epoch = decimal.Decimal(client.getTime()['epoch'])

    epoch = decimal.Decimal(epoch)
    return epoch, ticker, order_book


def add_data2(table, epoch, ticker, order_book):
    # Add an item
    response = table.put_item(Item={
        'symbol': SYMBOL,
        'time': epoch,
        'ticker': ticker,
        'bids': order_book['bids'],
        'asks': order_book['asks'],
        'bitstamp': bitstamp.ticker('btcusd')['last'],

    })

    return response


def to_decimal_type(d):
    for k, v in d.iteritems():
        if isinstance(v, basestring):
            try:
                d[k] = decimal.Decimal(v)
            except decimal.InvalidOperation:
                pass
            except Exception as e:
                raise e

"""
