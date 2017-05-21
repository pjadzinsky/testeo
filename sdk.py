import base64
import hashlib
import requests
import time

import credentials


def deribit_signature(nonce, uri, params, access_key, access_secret):
    sign = '_={0}&_ackey={1}&_acsec={2}&_action={3}'.format(nonce, access_key, access_secret, uri)
    for key in sorted(params.keys()):
        sign += '&{0}={1}'.format(key, params[key])
    
    return "{0}.{1}.{2}".format(access_key, nonce, base64.b64encode(hashlib.sha256(sign).digest()))


def get_instruments():
    response = requests.get('https://www.deribit.com/api/v1/public/getinstruments').json()

    if response['success']:
        return response['result']
    else:
        raise RuntimeError



def get_account():
    uri = 'https://www.deribit.com/api/v1/private/account'
    params = {}
    nonce = int(time.time() * 1000)
    access_key = credentials.KEY
    access_secret = credentials.SECRET
    response = requests.get(deribit_signature(nonce, uri, params, access_key, access_secret)).json()
    return response

