#!/bin/bash

aws lambda invoke \
    --invocation-type Event \
    --function-name main \
    --region us-west-2 \
    --payload file://inputfile.txt \
    --profile user2 \
    outputfile.txt
