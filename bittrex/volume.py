from bittrex import bittrex
from testeo import credentials

client = bittrex.Bittrex(credentials.BITTREX_KEY, credentials.BITTREX_SECRET)
print client.get_balance()