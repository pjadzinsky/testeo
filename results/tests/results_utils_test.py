#!/usr/bin/python
import unittest

import pandas as pd
import numpy as np

from results import results_utils

class TestClass(unittest.TestCase):
    def test_compute_percentage_from_baseline(self):
        baseline = pd.DataFrame({'value': range(10, 60, 10), 'time': range(1, 6)})
        data = pd.DataFrame({'value': [30], 'time': [4]})
        computed = results_utils.compute_percentage_from_baseline(baseline, data)
        expected = (30 - 40) / 40
        self.assertAlmostEqual(computed, expected)

    def test_compute_rate(self):
        for i in range(10):
            # try it 10 times with random 'rate'
            rate = np.random.rand() + 0.5
            data = pd.DataFrame({'time': range(1, 10), 'value': [rate ** i for i in range(1, 10)]})

            computed = results_utils.compute_rate(data)
            expected = rate
            self.assertAlmostEqual(computed, expected)

if __name__ == "__main__":
    unittest.main()
