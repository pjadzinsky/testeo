#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pprint

import table_manager
import populate_table


def main():
    table = table_manager.get_or_create_table()

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
