import boto3

import config

TABLE_NAME = config.TABLE_NAME


def get_or_create_table(key, secret, region):
    client = boto3.client('dynamodb', aws_access_key_id=key,
                          aws_secret_access_key=secret, region_name=region)

    response = client.list_tables()
    print response
    if TABLE_NAME not in response['TableNames']:
        table = _create_order_book_table(key, secret)
    else:
        table = boto3.resource('dynamodb', aws_access_key_id=key,
                                      aws_secret_access_key=secret).Table(TABLE_NAME)

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)

    # Print out some data about the table.
    return table


def _create_order_book_table(key, secret):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=key,
                              aws_secret_access_key=secret)
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {
                'AttributeName': 'symbol',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'time',
                'KeyType': 'RANGE',
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'symbol',
                'AttributeType': 'S',
            },
            {
                'AttributeName': 'time',
                'AttributeType': 'N',
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1,
        }
    )

    return table
