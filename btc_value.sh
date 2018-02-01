#!/bin/bash
. credentials.sh 0 0
python -c 'from exchanges import exchange; print "Bittrex: {}BTC".format(exchange.btc_value())'
. credentials.sh 1 0
python -c 'from exchanges import exchange; print "Poloniex: {}BTC".format(exchange.btc_value())'
