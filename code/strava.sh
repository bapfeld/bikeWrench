#!/bin/bash

python3 strava.py \
        --db_file='~/strava/data/strava.db' \
        --rider_name='Brendan' \
        --ini_path='~/strava/code/strava.ini' \
        --schema_path='~/strava/code/create_db.sql'
