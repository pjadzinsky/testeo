import base64
import hashlib
import requests
import time

import credentials
BASE_URL = 'https://www.deribit.com'

KEY = credentials.DERIBIT_KEY
SECRET = credentials.DERIBIT_SECRET


def deribit_signature(tstamp, uri, params, key, secret, debug=False):
    sign = '_={0}&_ackey={1}&_acsec={2}&_action={3}'.format(tstamp, key, secret, uri)
    for key in sorted(params.keys()):
        sign += '&{0}={1}'.format(key, params[key])
    
    if debug:
        print sign
    return "{0}.{1}.{2}".format(key, tstamp, base64.b64encode(hashlib.sha256(sign).digest()))


def get_instruments():
    response = requests.get(BASE_URL + '/api/v1/public/getinstruments').json()

    if response['success']:
        return response['result']
    else:
        raise RuntimeError


def get_account(tstamp=None, debug=False):
    uri = '/api/v1/private/account'
    if not tstamp:
        tstamp = int(time.time() * 1000)
    params = {}
    headers = {
            'x-deribit-sig': deribit_signature(tstamp, uri, params, KEY, SECRET, debug=debug)
    }
    if debug:
        print headers
    response = requests.get(BASE_URL + uri, headers=headers).json()
    return response


def buy(params, tstamp=None, debug=False):
    uri = '/api/v1/private/buy'

    if not tstamp:
        tstamp = int(time.time() * 1000)

    signature = {
            'x-deribit-sig': deribit_signature(tstamp, uri, params, KEY, SECRET, debug=debug)
    }
    if debug:
        print params

    response = requests.post(BASE_URL + uri, params, signature).json()
    return response

    
def compare_strings(str1, str2):

    if str1 == str2:
        return True
    for i, (a, b) in enumerate(zip(str1, str2)):
        if a == b:
            pass
        else:
            print i, a, b
