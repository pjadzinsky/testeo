import boto3
#import credentials
import config

TABLE_NAME = config.TABLE_NAME


def get_or_create_table():
    client = boto3.client('dynamodb')

    response = client.list_tables()

    if TABLE_NAME not in response['TableNames']:
        table = _create_order_book_table()
    else:
        table = boto3.resource('dynamodb').Table(TABLE_NAME)

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)

    # Print out some data about the table.
    return table


def _create_order_book_table():
    dynamodb = boto3.resource('dynamodb')
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
