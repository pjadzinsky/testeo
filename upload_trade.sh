#!/bin/bash

# This script will do everything necessary to generate a Lambda Deployment Package, it follows instructions
# from http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
# It encrypts sensitive KEY/PASSWORD information using aws KMS
#
# In short, the steps of the script are:
#   0. Make sure we have no left ofer PUDB statements
#   1. Delete Folder and all its contents
#   2. Make a folder
#   3. Put all necessary files in it
#   4. Add pip packages
#   5. Zip Folder
#   6. upload to s3

#Constants and variables
FOLDER=upload_trade

#   0. Make sure we have no left ofer PUDB statements
pudb_lines=$(grep -R --exclude=upload_trade.sh --exclude=to_upload.zip PUDB)
pudb_cnt=$(echo $pudb_lines | wc -w)
echo $pudb_cnt
if [ $pudb_cnt -gt 0 ]; then
    echo $pudb_cnt
    echo $pudb_lines
    exit
fi

echo 1
#   1. Delete Folder and all its contents
#rm -rf $FOLDER/*
#rmdir $FOLDER

echo 2
#   2. Make a folder and correct tree structrue
mkdir $FOLDER

echo 3
#   3. Put all necessary files in it
cp -r portfolio $FOLDER
cp -r market $FOLDER
cp bittrex_utils.py $FOLDER
cp config.py $FOLDER
cp memoize.py $FOLDER
cp report.py $FOLDER
cp s3_utils.py $FOLDER
cp state.py $FOLDER
cp trade.py $FOLDER
cp utils.py $FOLDER

echo 4
#   4. Add pip packages
for package in {bittrex,pandas,python-gflags,numpy}; do
    if [ ! -d "$FOLDER/$package" ]; then
        pip install $package -t $FOLDER
    fi
done

echo 5
#   5. Zip Folder
pushd $FOLDER
files=$(ls)
zip -r ../${FOLDER}.zip $files
popd

echo 6
#   6. upload to s3
aws s3 cp ${FOLDER}.zip s3://my-lambda-func/trade.zip --profile user2

# Encrypt env variables
#aws kms encrypt --key-id arn:aws:kms:us-west-2:703012228455:key/0e0e46cf-89e3-4dc2-a789-b3f77d991459 \
#    --plaintext \
#    --profile user2 \
#    --region us-west-2 \
#    14c66e5b99684569b91de281d238953b


