#!/usr/bin/python
import unittest

import utime

class TestClass(unittest.TestCase):
    def test1(self):
        d = utime.utime.from_timestamp(1)
        s = d.datetime.isoformat()
        self.assertEqual(s, "1970-01-01T00:00:01+00:00")

    def test2(self):
        d = utime.utime.from_iso("1970-01-01T00:00:01+00:00")

        self.assertEqual(d.to_timestamp(), 1)


if __name__ == "__main__":
    unittest.main()
