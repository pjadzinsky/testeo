output=$(aws kms encrypt --key-id arn:aws:kms:us-west-2:703012228455:key/0e0e46cf-89e3-4dc2-a789-b3f77d991459 \
    --plaintext \
    --profile user2 \
    --region us-west-2 \
    --output text \
    --query CiphertextBlob \
    $1)

echo $output

