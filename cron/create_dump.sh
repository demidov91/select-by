#!/usr/bin/env bash

export PGPASSWORD=$POSTGRES_PASSWORD
pg_dump -h postgres -U postgres |gzip > /tmp/dump.gz
aws s3 mv /tmp/dump.gz s3://$DUMP_BUCKET/`date +%Y-%m-%d`.gz