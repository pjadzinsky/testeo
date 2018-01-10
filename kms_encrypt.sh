#!/bin/bash

string_to_encrypt=$1

aws kms encrypt \
    --profile user2 \
    --key-id my_cool_key \
    --plaintext $string_to_encrypt \
    --output text \
    --query CiphertextBlob | base64 --decode > ExampleEncryptedFile