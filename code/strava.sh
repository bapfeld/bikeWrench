#!/bin/bash

python3 ~/stravaDB/code/strava.py \
        --schema_path=~/stravaDB/code/create_db.sql \
        --bike_part_json_path=~/stravaDB/code/bike_parts.json
