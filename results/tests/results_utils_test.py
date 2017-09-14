#!/usr/bin/python
import unittest

import pandas as pd
import numpy as np

from results import results_utils

class TestClass(unittest.TestCase):
    def test_compute_mean_percentage(self):
        data = pd.DataFrame({'value': [10, 20, 5], 'time': [0, 1, 2]})
        results_utils.compute_mean_percentage(data)
        computed = data['mean percentage']
        expected = [np.NaN, 100, -25]
        print computed
        print expected
        self.assertItemsEqual(computed.values[1:], expected[1:])
        self.assertTrue(np.isnan(computed.values[0]))

    def test_compute_rate(self):
        for i in range(10):
            # try it 10 times with random 'rate'
            rate = np.random.rand() + 0.5
            data = pd.DataFrame({'time': range(0, 10), 'value': [rate ** i for i in range(0, 10)]})

            results_utils.compute_rate(data)
            computed = data['rate'].values
            expected = rate
            self.assertTrue(np.isnan(computed[0]))
            for i in range(1, 10):
                self.assertAlmostEqual(computed[i], expected)

if __name__ == "__main__":
    unittest.main()
