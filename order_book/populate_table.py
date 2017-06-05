import GDAX
import decimal

SYMBOL = 'BTC-USD'


def get_data():
    client = GDAX.PublicClient()
    order_book = client.getProductOrderBook(product=SYMBOL, level=2)
    ticker = client.getProductTicker(SYMBOL)
    epoch = decimal.Decimal(client.getTime()['epoch'])

    epoch = decimal.Decimal(epoch)
    return epoch, ticker, order_book


def add_data(table, epoch, ticker, order_book):
    # Add an item
    response = table.put_item(Item={
        'symbol': SYMBOL,
        'time': epoch,
        'ticker': ticker,
        'bids': order_book['bids'],
        'asks': order_book['asks']
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

