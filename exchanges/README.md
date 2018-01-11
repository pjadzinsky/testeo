Differences and similarities between Bittrex/Yobit/Poloniex APIs
The goal is to come up with a unified design that can be used across multiple exchanges


   
### Market/Ticker

POLONIEX PUBLIC API
returnTicker
```python
{"BTC_LTC":{
    "last":"0.0251",
    "lowestAsk":"0.02589999",
    "highestBid":"0.0251",
    "percentChange":"0.02390438",
    "baseVolume":"6.16485315",
    "quoteVolume":"245.82513926"
    },
"BTC_NXT":{
    "last":"0.00005730",
    "lowestAsk":"0.00005710",
    "highestBid":"0.00004903",
    "percentChange":"0.16701570",
    "baseVolume":"0.45347489",
    "quoteVolume":"9094"},
     ...
}
```            
BITTREX PUBLIC API
getmarketsummaries
```python
[
    {
        "MarketName" : "BTC-888",
        "High" : 0.00000919,
        "Low" : 0.00000820,
        "Volume" : 74339.61396015,
        "Last" : 0.00000820,
        "BaseVolume" : 0.64966963,
        "TimeStamp" : "2014-07-09T07:19:30.15",
        "Bid" : 0.00000820,
        "Ask" : 0.00000831,
        "OpenBuyOrders" : 15,
        "OpenSellOrders" : 15,
        "PrevDay" : 0.00000821,
        "Created" : "2014-03-20T06:00:00",
        "DisplayMarketName" : null
    }, {
        "MarketName" : "BTC-A3C",
        "High" : 0.00000072,
        "Low" : 0.00000001,
        "Volume" : 166340678.42280999,
        "Last" : 0.00000005,
        "BaseVolume" : 17.59720424,
        "TimeStamp" : "2014-07-09T07:21:40.51",
        "Bid" : 0.00000004,
        "Ask" : 0.00000005,
        "OpenBuyOrders" : 18,
        "OpenSellOrders" : 18,
        "PrevDay" : 0.00000002,
        "Created" : "2014-05-30T07:57:49.637",
        "DisplayMarketName" : null
    }
]

```
BITTREX PUBLIC API
getmarkets
```python
[{
        "MarketCurrency" : "LTC",
        "BaseCurrency" : "BTC",
        "MarketCurrencyLong" : "Litecoin",
        "BaseCurrencyLong" : "Bitcoin",
        "MinTradeSize" : 0.01000000,
        "MarketName" : "BTC-LTC",
        "IsActive" : true,
        "Created" : "2014-02-13T00:00:00"
    }, {
        "MarketCurrency" : "DOGE",
        "BaseCurrency" : "BTC",
        "MarketCurrencyLong" : "Dogecoin",
        "BaseCurrencyLong" : "Bitcoin",
        "MinTradeSize" : 100.00000000,
        "MarketName" : "BTC-DOGE",
        "IsActive" : true,
        "Created" : "2014-02-13T00:00:00"
    }]
```

### Currencies

POLONIEX PUBLIC API
returnCurrencies
Returns information about currencies. Sample output:
```python
{
    "1CR":{
        "maxDailyWithdrawal":10000,
        "txFee":0.01,
        "minConf":3,
        "disabled":0
    },
    "ABY":{
        "maxDailyWithdrawal":10000000,
        "txFee":0.01,
        "minConf":8,
        "disabled":0
    },
    ...
}
```

```python
[
    {
        "Currency" : "BTC",
        "CurrencyLong" : "Bitcoin",
        "MinConfirmation" : 2,
        "TxFee" : 0.00020000,
        "IsActive" : true,
        "CoinType" : "BITCOIN",
        "BaseAddress" : null
    }, {
        "Currency" : "LTC",
        "CurrencyLong" : "Litecoin",
        "MinConfirmation" : 5,
        "TxFee" : 0.00200000,
        "IsActive" : true,
        "CoinType" : "BITCOIN",
        "BaseAddress" : null
    }
]
```

### Balances
POLONIEX PRIVATE API
returnBalances
    Returns all of your available balances. Sample output:
```python
{
    "BTC":"0.59098578",
    "LTC":"3.31117268",
}
```

POLONIEX PRIVATE API
returnCompleteBalances
    Returns all of your balances, including available balance, balance on orders, and the estimated BTC value of your
    balance. By default, this call is limited to your exchange account; set the "account" POST parameter to "all" to
    include your margin and lending accounts. Sample output:
```python
{
    "LTC":{
        "available":"5.015",
        "onOrders":"1.0025",
        "btcValue":"0.078"
        },
    "NXT:{...}
    ...
}
```

BITTREX PRIVATE API
```python
[
    {
        "Currency" : "DOGE",
        "Balance" : 0.00000000,
        "Available" : 0.00000000,
        "Pending" : 0.00000000,
        "CryptoAddress" : "DLxcEt3AatMyr2NTatzjsfHNoB9NT62HiF",
        "Requested" : false,
        "Uuid" : null
    }, {
        "Currency" : "BTC",
        "Balance" : 14.21549076,
        "Available" : 14.21549076,
        "Pending" : 0.00000000,
        "CryptoAddress" : "1Mrcdr6715hjda34pdXuLqXcju6qgwHA31",
        "Requested" : false,
        "Uuid" : null
    }
]
```

### Deposits/Withdrawals
POLONIEX PRIVATE API
returnDepositsWithdrawals
    Returns your deposit and withdrawal history within a range, specified by the "start" and "end" POST parameters, both of which should be given as UNIX timestamps. Sample output:

```python
{"deposits":
    [{
        "currency":"BTC",
        "address":"...",
        "amount":"0.01006132",
        "confirmations":10,
        "txid":"17f819a91369a9ff6c4a34216d434597cfc1b4a3d0489b46bd6f924137a47701",
        "timestamp":1399305798,
        "status":"COMPLETE"
     }, {
        "currency":"BTC",
        "address":"...",
        "amount":"0.00404104",
        "confirmations":10,
        "txid":"7acb90965b252e55a894b535ef0b0b65f45821f2899e4a379d3e43799604695c",
        "timestamp":1399245916,
        "status":"COMPLETE"
     }],
 "withdrawals":
    [{
        "withdrawalNumber":134933,
        "currency":"BTC",
        "address":"1N2i5n8DwTGzUq2Vmn9TUL8J1vdr1XBDFg",
        "amount":"5.00010000",
        "timestamp":1399267904,
        "status":"COMPLETE: 36e483efa6aff9fd53a235177579d98451c4eb237c210e66cd2b9a2d4a988f8e",
        "ipAddress":"..."
    }]
}
```

BITTREX PRIVATE API
getwithdrawayhistory
getdeposithistory
```python
[
    {
        "PaymentUuid" : "b52c7a5c-90c6-4c6e-835c-e16df12708b1",
        "Currency" : "BTC",
        "Amount" : 17.00000000,
        "Address" : "1DeaaFBdbB5nrHj87x3NHS4onvw1GPNyAu",
        "Opened" : "2014-07-09T04:24:47.217",
        "Authorized" : true,
        "PendingPayment" : false,
        "TxCost" : 0.00020000,
        "TxId" : null,
        "Canceled" : true,
        "InvalidAddress" : false
    }, {
        "PaymentUuid" : "f293da98-788c-4188-a8f9-8ec2c33fdfcf",
        "Currency" : "XC",
        "Amount" : 7513.75121715,
        "Address" : "XVnSMgAd7EonF2Dgc4c9K14L12RBaW5S5J",
        "Opened" : "2014-07-08T23:13:31.83",
        "Authorized" : true,
        "PendingPayment" : false,
        "TxCost" : 0.00002000,
        "TxId" : "b4a575c2a71c7e56d02ab8e26bb1ef0a2f6cf2094f6ca2116476a569c1e84f6e",
        "Canceled" : false,
        "InvalidAddress" : false
    }
]
```

### Open Orders
POLONIEX PRIVATE API
returnOpenOrders
    Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP".
    Set "currencyPair" to "all" to return open orders for all markets. Sample output for single market:
```python
[
    {
        "orderNumber":"120466",
        "type":"sell",
        "rate":"0.025",
        "amount":"100",
        "total":"2.5"},
    {
        "orderNumber":"120467",
        "type":"sell",
        "rate":"0.04",
        "amount":"100",
        "total":"4"
    },
    ...
]
```

    Or, for all markets:

```python
{
    "BTC_1CR":[],
    "BTC_AC":[{
        "orderNumber":"120466",
        "type":"sell",
        "rate":"0.025",
        "amount":"100",
        "total":"2.5"
        }, {
        "orderNumber":"120467",
        "type":"sell",
        "rate":"0.04",
        "amount":"100",
        "total":"4"}],
     ...
}
```

BITTREX PRIVATE API
getopenorders
```python
 [{
			"Uuid" : null,
			"OrderUuid" : "09aa5bb6-8232-41aa-9b78-a5a1093e0211",
			"Exchange" : "BTC-LTC",
			"OrderType" : "LIMIT_SELL",
			"Quantity" : 5.00000000,
			"QuantityRemaining" : 5.00000000,
			"Limit" : 2.00000000,
			"CommissionPaid" : 0.00000000,
			"Price" : 0.00000000,
			"PricePerUnit" : null,
			"Opened" : "2014-07-09T03:55:48.77",
			"Closed" : null,
			"CancelInitiated" : false,
			"ImmediateOrCancel" : false,
			"IsConditional" : false,
			"Condition" : null,
			"ConditionTarget" : null
		}, {
			"Uuid" : null,
			"OrderUuid" : "8925d746-bc9f-4684-b1aa-e507467aaa99",
			"Exchange" : "BTC-LTC",
			"OrderType" : "LIMIT_BUY",
			"Quantity" : 100000.00000000,
			"QuantityRemaining" : 100000.00000000,
			"Limit" : 0.00000001,
			"CommissionPaid" : 0.00000000,
			"Price" : 0.00000000,
			"PricePerUnit" : null,
			"Opened" : "2014-07-09T03:55:48.583",
			"Closed" : null,
			"CancelInitiated" : false,
			"ImmediateOrCancel" : false,
			"IsConditional" : false,
			"Condition" : null,
			"ConditionTarget" : null
		}
	]
```

POLONIEX PRIVATE API
returnTradeHistory
    Returns your trade history for a given market, specified by the "currencyPair" POST parameter.
    You may specify "all" as the currencyPair to receive your trade history for all markets. You may optionally specify
    a range via "start" and/or "end" POST parameters, given in UNIX timestamp format; if you do not specify a range,
    it will be limited to one day. You may optionally limit the number of entries returned using the "limit" parameter,
    up to a maximum of 10,000. If the "limit" parameter is not specified, no more than 500 entries will be returned.
    Sample output:

    [{ "globalTradeID": 25129732, "tradeID": "6325758", "date": "2016-04-05 08:08:40", "rate": "0.02565498", "amount": "0.10000000", "total": "0.00256549", "fee": "0.00200000", "orderNumber": "34225313575", "type": "sell", "category": "exchange" }, { "globalTradeID": 25129628, "tradeID": "6325741", "date": "2016-04-05 08:07:55", "rate": "0.02565499", "amount": "0.10000000", "total": "0.00256549", "fee": "0.00200000", "orderNumber": "34225195693", "type": "buy", "category": "exchange" }, ... ]

    Or, for all markets:

    {"BTC_MAID": [ { "globalTradeID": 29251512, "tradeID": "1385888", "date": "2016-05-03 01:29:55", "rate": "0.00014243", "amount": "353.74692925", "total": "0.05038417", "fee": "0.00200000", "orderNumber": "12603322113", "type": "buy", "category": "settlement" }, { "globalTradeID": 29251511, "tradeID": "1385887", "date": "2016-05-03 01:29:55", "rate": "0.00014111", "amount": "311.24262497", "total": "0.04391944", "fee": "0.00200000", "orderNumber": "12603319116", "type": "sell", "category": "marginTrade" }, ... ],"BTC_LTC":[ ... ] ... }


POLONIEX PRIVATE API
returnOrderTrades
    Returns all trades involving a given order, specified by the "orderNumber" POST parameter. If no trades for the
    order have occurred or you specify an order that does not belong to you, you will receive an error. Sample output:

    [{"globalTradeID": 20825863, "tradeID": 147142, "currencyPair": "BTC_XVC", "type": "buy", "rate": "0.00018500", "amount": "455.34206390", "total": "0.08423828", "fee": "0.00200000", "date": "2016-03-14 01:04:36"}, ...]

## Buy
POLONIEX PRIVATE API
buy
    Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If
    successful, the method will return the order number. Sample output:

    You may optionally set "fillOrKill", "immediateOrCancel", "postOnly" to 1. A fill-or-kill order will either fill
    in its entirety or be completely aborted. An immediate-or-cancel order can be partially or completely filled, but
    any portion of the order that cannot be filled immediately will be canceled rather than left on the order book.
    A post-only order will only be placed if no portion of it fills immediately; this guarantees you will never pay the
    taker fee on any part of the order that fills.
```python
{
    "orderNumber":31226040,
    "resultingTrades":[{
        "amount":"338.8732",
        "date":"2014-10-18 23:03:21",
        "rate":"0.00000173",
        "total":"0.00058625",
        "tradeID":"16164",
        "type":"buy"}]
    }
```

BITTREX PRIVATE API
buylimit, requires "market", "quantity" and "rate"
```python
{
    "uuid" : "e606d53c-8d70-11e3-94b5-425861b86ab6"
}
```

### Sell
POLONIEX PRIVATE API
sell
    Places a sell order in a given market. Parameters and output are the same as for the buy method.
BITTREX PRIVATE API
selllimit, also like buylimit

### Cancel
POLONIEX PRIVATE API
cancelOrder
    Cancels an order you have placed in a given market. Required POST parameter is "orderNumber". If successful, the method will return:
```python
{"success":1}
```

BITTREX PRIVATE API
cancel, requires "uuid"
```python
{
    "success" : true,
    "message" : "",
    "result" : null
}
```

### MoveOrder
POLONIEX PRIVATE API
moveOrder
    Cancels an order and places a new one of the same type in a single atomic transaction, meaning either both operations will succeed or both will fail. Required POST parameters are "orderNumber" and "rate"; you may optionally specify "amount" if you wish to change the amount of the new order. "postOnly" or "immediateOrCancel" may be specified for exchange orders, but will have no effect on margin orders. Sample output:

    {"success":1,"orderNumber":"239574176","resultingTrades":{"BTC_BTS":[]}}


POLONIEX PRIVATE API
returnFeeInfo
    If you are enrolled in the maker-taker fee schedule, returns your current trading fees and trailing 30-day volume
    in BTC. This information is updated once every 24 hours.

    {"makerFee": "0.00140000", "takerFee": "0.00240000", "thirtyDayVolume": "612.00248891", "nextTier": "1200.00000000"}


POLONIEX PUBLIC API
return24Volume
    Returns the 24-hour volume for all markets, plus totals for primary currencies. Sample output:
    {"BTC_LTC":{"BTC":"2.23248854","LTC":"87.10381314"},"BTC_NXT":{"BTC":"0.981616","NXT":"14145"}, ... "totalBTC":"81.89657704","totalLTC":"78.52083806"}


POLONIEX PUBLIC API
returnTradeHistory
    Returns the past 200 trades for a given market, or up to 50,000 trades between a range specified in UNIX timestamps by the "start" and "end" GET parameters. Sample output:
    [{"date":"2014-02-10 04:23:23","type":"buy","rate":"0.00007600","amount":"140","total":"0.01064"},{"date":"2014-02-10 01:19:37","type":"buy","rate":"0.00007600","amount":"655","total":"0.04978"}, ... ]

