#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

import test1


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
        computed = test1.deribit_signature(tstamp, action, params, key, secret)
        print expected
        print computed

        self.assertEqual(expected, computed)


if __name__ == "__main__":
    unittest.main()
