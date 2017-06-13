import hashlib
import hmac
import requests
import time

import credentials
BASE_URL = 'https://www.bitstamp.net/api/v2/'


def ticker(symbol):
    return _public_request('ticker', symbol)


def hourly_ticker(symbol):
    return _public_request('ticker_hourly', symbol)


def order_book(symbol):
    return _public_request('order_book', symbol)


def transactions(symbol):
    return _public_request('transactions', symbol)


def balance():
    uri = 'balance/'
    return _private_request(uri, {})


def user_transactions():
    uri = 'user_transactions/'
    return _private_request(uri, {})


def open_orders(symbol):
    _verify_symbol(symbol)
    uri = 'open_orders/{}/'.format(symbol)
    return _private_request(uri, {})


def order_status(order_id):
    assert(isinstance(order_id, basestring))
    uri = 'order_status/'
    return _private_request(uri, {'id': order_id})


def cancel_order(order_id):
    assert(isinstance(order_id, basestring))
    uri = 'cancel_order/'
    return _private_request(uri, {'id': order_id})


def buy_limit_order(symbol, amount, price, limit_price):
    _verify_symbol(symbol)
    uri = 'buy/{}/'.format(symbol)
    params = {'amount': amount, 'price': price, 'limit_price': limit_price}
    return _private_request(uri, params)


def buy_market_order(symbol, amount):
    _verify_symbol(symbol)
    uri = 'buy/market/{}/'.format(symbol)
    params = {'amount': amount}
    return _private_request(uri, params)


def buy_stop_order(symbol, amount, price):
    _verify_symbol(symbol)
    uri = 'buy/stop/{}/'.format(symbol)
    params = {'amount': amount, 'price': price}
    return _private_request(uri, params)
    pass


def sell_limit_order(symbol, amount, price, limit_price):
    _verify_symbol(symbol)
    uri = 'sell/{}/'.format(symbol)
    params = {'amount': amount, 'price': price, 'limit_price': limit_price}
    return _private_request(uri, params)


def sell_market_order(symbol, amount):
    _verify_symbol(symbol)
    uri = 'sell/market/{}/'.format(symbol)
    params = {'amount': amount}
    return _private_request(uri, params)


def _public_request(endpoint, symbol):
    uri = BASE_URL + endpoint

    if symbol:
        _verify_symbol(symbol)
        uri += '/{0}/'.format(symbol)

    print uri
    response = requests.get(uri).json()
    return response


def _private_request(uri, params):
    nonce = _get_nonce()
    params.update({'key': credentials.BITSTAMP_KEY,
                   'signature': _get_signature(nonce),
                   'nonce': nonce})
    uri = BASE_URL + uri
    print params
    return requests.post(uri, data=params).json()


def _verify_symbol(symbol):
    assert(symbol in ['all', 'btcusd', 'btceur', 'eurusd', 'xrpusd', 'xrpeur',
                      'xrpbtc'])


def _get_nonce():
    return str(int(time.time()*1000))


def _get_signature(nonce):

    message = nonce + credentials.BITSTAMP_CUSTOMER_ID + credentials.BITSTAMP_KEY
    signature = hmac.new(
        credentials.BITSTAMP_SECRET,
        msg=message,
        digestmod=hashlib.sha256
    ).hexdigest().upper()

    return signature


