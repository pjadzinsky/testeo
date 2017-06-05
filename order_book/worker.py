#!/usr/bin/env python
# -*- coding: utf-8 -*-
import create_table
import populate_table


def main():
    table = create_table.get_or_create_table()

    epoch, ticker, order_book = populate_table.get_data()
    response = populate_table.add_data(table, epoch, ticker, order_book)

    print response


if __name__ == "__main__":
    main()
