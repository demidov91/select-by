#!/usr/bin/env bash

export PGPASSWORD=$POSTGRES_PASSWORD
aws s3 cp s3://$DUMP_BUCKET/$1 /tmp/$1
gunzip -c /tmp/$1|psql -U postgres -h postgres
rm /tmp/$1