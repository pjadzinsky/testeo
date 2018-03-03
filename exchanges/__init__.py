import os

from exchanges import bittrex_utils
from exchanges import poloniex_utils

if os.environ['EXCHANGE'] == 'POLONIEX':
    exchange = poloniex_utils.Exchange()
    exchange.MINIMUM_TRADE = 10000    # in SAT (satoshis)
elif os.environ['EXCHANGE'] == 'BITTREX':
    exchange = bittrex_utils.Exchange()
    exchange.MINIMUM_TRADE = 100000 # in SAT (satoshis)
else:
    raise NotImplementedError

