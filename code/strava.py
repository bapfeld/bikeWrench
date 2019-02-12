from stravalib.client import Client
import configparser
import sqlite3
import os, sys
import pandas as pd

class my_db():
    """Class to operate on a database

    """
    def __init__(self, db_path):
        self.db_path = db_path

    def insert_to_db(self, table, tb_dict):
        # construct the command
        command = 'insert into ' + table + '('
        for k, v in tb_dict.items():
            command += k + ' '
        command = command.rstrip()
        command += ')\nvalues('
        for k, v in tb_dict.items():
            command += v + ' '
        command = command.rstrip()
        command += ')'
        # run the command
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(command)

    def strava_activity_to_db(self, activity):
        tbl = {'id': activity.id,
               'bike': activity.gear.id,
               'distance': float(activity.distance),
               'name': activity.name,
               'moving_time': activity.moving_time.seconds,
               'elapsed_time': activity.elapsed_time.seconds,
               'elev': float(activity.total_elevation_gain),
               'type': activity.type,
               'avg_speed': float(activity.average_speed),
               'max_speed': float(activity.max_speed),
               'calories': float(activity.calories)}

    def get_from_db(self, query):
        # execute the command
        with sqlite3.connect(db_filename) as conn:
            self.res = pd.read_sql_query(query, conn)
            

        
        
# Let's start by building up a temporary database
db_file = 'strava.db'
db_path = os.path.expanduser('~/strava/data/' + db_file)
schema_file = 'create_db.sql'
schema_path = os.path.expanduser('~/strava/code/' + schema_file)
db_is_new = not os.path.exists(db_path)

with sqlite3.connect(db_path) as conn:
    if db_is_new:
        print('Creating schema')
        with open(schema_path, 'rt') as f:
            schema = f.read()
        conn.executescript(schema)

        print('Inserting initial data')
        
        conn.execute("""
        insert into riders (name, dob, weight, fthr)
        values ('Brendan', '1988-06-06', '165', '190')
        """)
        
        conn.execute("""
        insert into bikes (id, name, color, purchased, price, rider)
        values ('b3671458', 'SuperSix Evo', 'Black and Green', '2016-01-03', '1800', 'Brendan')
        """)
        
    else:
        print('Database exists, assume schema does, too.')


# Functions to interact!
# start by creating our object
db = my_db(db_path)

