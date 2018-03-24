# When creating new keys, don't forget to enable them and make sure --region is the same as in the key
# ALso, the profile has to be added to the Encryption Key in IAM

output=$(aws kms encrypt \
    --key-id arn:aws:kms:us-west-2:703012228455:key/0e0e46cf-89e3-4dc2-a789-b3f77d991459 \
    --plaintext \
    --profile pablo \
    --region us-west-2 \
    --output text \
    --query CiphertextBlob \
    $1)

echo $output

