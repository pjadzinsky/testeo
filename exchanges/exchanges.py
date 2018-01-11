import os

from exchanges import bittrex_utils
from exchanges import poloniex_utils

"""
if os.environ['EXCHANGE'] == 'POLONIEX':
    class Exchange(bittrex_utils.Exchange):
        pass

    #Exchange = poloniex_utils.Exchange
elif os.environ['EXCHANGE'] == 'BITTREX':
    class Exchange(poloniex_utils):
        pass
    #Exchange = bittrex_utils.Exchange
else:
    raise NotImplementedError
"""
