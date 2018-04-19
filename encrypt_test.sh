# When creating new keys, don't forget to enable them and make sure --region is the same as in the key
# ALso, the profile has to be added to the Encryption Key in IAM

if [[ $LOGNAME == "pablo" ]]; then
    echo pablo
    profile=pablo
elif [[ $LOGNAME == "adrian" ]]; then
    echo adrian
    profile=adiran
else
    echo "Error! env variale LOGNAME=$LOGNAME not recognized" 1>&2
    exit 64
fi

encrypted=$(aws kms encrypt \
    --key-id arn:aws:kms:us-west-2:703012228455:key/0e0e46cf-89e3-4dc2-a789-b3f77d991459 \
    --plaintext \
    --profile $profile \
    --region us-west-2 \
    --output text \
    --query CiphertextBlob \
    $1)

echo $encrypted
