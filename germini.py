import requests
import urllib2

import credentials

BASE_URL = "https://api.sandbox.gemini.com/v1/"


def get_symbols():
    # or, for sandbox

    return _public_request('symbols', None)


def ticker(symbol):
    # or, for sandbox
    _verify_symbol(symbol)

    return _public_request('pubticker/', symbol)


def order_book(symbol):
    _verify_symbol(symbol)

    return _public_request('book/', symbol)


def current_auction(symbol):
    _verify_symbol(symbol)

    return _public_request('auction/', symbol)


def _public_request(endpoint, symbol):
    url = BASE_URL + endpoint

    if symbol:
        url += symbol

    print url
    response = urllib2.urlopen(url)
    return response.read()


def _verify_symbol(symbol):
    assert(symbol in ['btcusd', 'ethbtc', 'ethusd'])
