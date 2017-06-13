import krakenex


public_client = krakenex.API()


def ticker(symbol):
    answer = public_client.query_public('Ticker', {'pair': symbol})

    if answer['error']:
        raise RuntimeError
    else:
        return answer['result']


def asset_pairs():
    answer = public_client.query_public('AssetPairs')
    if answer['error']:
        raise RuntimeError
    else:
        return answer['result']
