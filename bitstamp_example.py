#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bitstamp


def main():
    bitstamp.sell_limit_order('xrpusd', 100, 1, None)
    print bitstamp.open_orders('all')


if __name__ == "__main__":
    main()
