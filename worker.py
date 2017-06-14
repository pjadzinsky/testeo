#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pprint

from order_book import populate_table
from order_book import table_manager
import credentials



def main():
    # table is flexible, we can define keys as we use it. The only required
    # keys are 'symbol' and 'time'
    import pudb
    pudb.set_trace()
    table = table_manager.get_or_create_table(credentials.AWS_KEY,
                                              credentials.AWS_SECRET,
                                              'us-west-2')

    response = populate_table.add_data(table)

    if response['ResponseMetadata'].get('HTTPStatusCode') == 200:
        pass
    else:
        pprint.pprint(response)

    scan = table.scan()
    print '#'*80
    pprint.pprint(scan['Items'])
    #pprint.pprint(table.describe_table())


if __name__ == "__main__":
    main()
