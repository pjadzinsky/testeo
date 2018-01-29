Things to do

1.  prod/staging should be use only to define the bucket we are writing to, never to read data from.
    Data should always be read from production and written to staging/prod buckets
1.  Write should always follow this pattern
    
    if account specific, write_bucket/account/s3_key    (for example a particular portfolio)
    if account independent, write_bucket/s3_key (for example hourly markets)
    
1.  Decouple environmental variable EXCHANGE_ACCOUNT from prod/staging
    I don't know what the variable for prod/staging should be call, but
    EXCHANGE_ACCOUNT should be pablo/account_1/ etc
    
1.  Clean code, remove dead code

1.  Change references to 'state' to use the 'new' csv in s3://echange-currencies/<EXCHANGE>/<ACCOUNT>/currencies.csv

1.  Withdrawal and deposits not working for bittrex