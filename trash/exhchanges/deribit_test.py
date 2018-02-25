#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

import sdk


class TestClass(unittest.TestCase):
    def test_signature(self):
        tstamp = 1452237485895
        key = '29mtdvvqV56'
        secret = 'BP2FEOFJLFENIYFBJI7PYWGFNPZOTRCE'
        action = '/api/v1/private/buy'
        params = {
            'instrument': 'BTC-15JAN16',
            'price': 500,
            'quantity': 1,
        }
        expected = '29mtdvvqV56.1452237485895.0nkPWTDunuuc220vojSTirSj8/2eGT8Wv30YeLj+i4c='
        computed = sdk.deribit_signature(tstamp, action, params, key, secret)

        self.assertEqual(expected, computed)


    def test_account(self):
        tstamp = 1495359724041

        print(sdk.get_account(tstamp=tstamp, debug=True))

if __name__ == "__main__":
    unittest.main()
