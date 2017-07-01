#!/usr/bin/python

import json
import unittest
import mock

from my_bittrex import volume


class TestClass(unittest.TestCase):
    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    def test_get_summaries(self, mocked_summaries):
        mocked_summaries.return_value = fake_get_summaries()
        print volume.get_summaries()

    @mock.patch('my_bittrex.volume.client.get_balances')
    def test_get_balances(self, mocked_balances):
        mocked_balances.return_value = fake_get_balances()
        print volume.get_balances()

    @mock.patch('my_bittrex.volume.client.get_balances')
    def test_rebalance(self, mocked_balances):
        mocked_balances.return_value = fake_get_balances()
        volume.rebalance()

        print 1

    @mock.patch('my_bittrex.volume.client.get_market_summaries')
    @mock.patch('my_bittrex.volume.client.get_balances')
    def test_total(self, mocked_balances, mocked_summaries):
        mocked_balances.return_value = fake_get_balances()
        mocked_summaries.return_value = fake_get_summaries()

        computed = volume.get_total_balance('BTC')
        print computed



def fake_get_summaries():
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
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
            }, {
                "MarketName" : "BTC-ETH",
                "High" : 0.2002,
                "Low" : 0.2001,
                "Volume" : 1.2,
                "Last" : 0.2,
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
    } """
    return json.loads(response)


def fake_get_balances():
    response = """ {
        "success" : true,
        "message" : "",
        "result" : [{
                "Currency" : "A3C",
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
            }, {
                "Currency" : "ETH",
                "Balance" : 10.123456,
                "Available" : 10.123456,
                "Pending" : 0.00000000,
                "CryptoAddress" : "1Mrcdr6715hjda34pdXuLqXcju6qgwHA31",
                "Requested" : false,
                "Uuid" : null
            }
        ]
    } """
    return json.loads(response)


if __name__ == "__main__":
    unittest.main()
