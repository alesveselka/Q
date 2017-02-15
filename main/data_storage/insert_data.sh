#!/usr/bin/env bash

export DB_HOST=localhost
export DB_NAME=norgate
export DB_USER=sec_user
export DB_PASS=root

python $(dirname $0)/norgate_data.py "$1"
