import os

from exchanges import bittrex_utils
from exchanges import poloniex_utils

if os.environ['EXCHANGE'] == 'POLONIEX':
    exchange = poloniex_utils.Exchange()
elif os.environ['EXCHANGE'] == 'BITTREX':
    exchange = bittrex_utils.Exchange()
else:
    raise NotImplementedError

