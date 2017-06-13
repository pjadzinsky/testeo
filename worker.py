#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pprint

from exchanges import bitstamp
from exchanges import deribit
from exchanges import germini

from order_book import table_manager
from order_book import populate_table


def main():
    # table is flexible, we can define keys as we use it. The only required
    # keys are 'symbol' and 'time'
    table = table_manager.get_or_create_table()

    # get 
    epoch, ticker, order_book = populate_table.get_data()
    response = populate_table.add_data(table, epoch, ticker, order_book)

    if response['ResponseMetadata'].get('HTTPStatusCode') == 200:
        pass
    else:
        pprint.pprint(response)

    scan = table.scan()
    #pprint.pprint(scan['Items'])
    pprint.pprint(table.describe_table())


if __name__ == "__main__":
    main()
