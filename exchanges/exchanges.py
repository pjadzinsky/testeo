import os

from exchanges import bittrex_utils
from exchanges import poloniex_utils

if os.environ['EXCHANGE'] == 'POLONIEX':
    Exchange = poloniex_utils.Exchange
elif os.environ['EXCHANGE'] == 'BITTREX':
    Exchange = bittrex_utils.Exchange
else:
    raise NotImplementedError
