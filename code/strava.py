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

    def strava_activity_to_db(self, activity, rider_name):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('insert into rides (id, bike, distance, name, moving_time, elapsed_time, elev, type, avg_speed, max_speed, calories, rider) values (?,?,?,?,?,?,?,?,?,?,?,?)', (activity.id, activity.gear.id, float(activity.distance), activity.name, activity.moving_time.seconds, activity.elapsed_time.seconds, float(activity.total_elevation_gain), activity.type, float(activity.average_speed), float(activity.max_speed), float(activity.calories), rider_name, ))

    def initialize_rides(self, activity_list, rider_name):
        a_list = [(a.id, a.gear.id, float(a.distance), a.name, a.moving_time.seconds, a.elapsed_time.seconds, float(a.total_elevation_gain), a.type, float(a.average_speed), float(a.max_speed), float(a.calories), rider_name, ) for a in activity_list]
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany('insert into rides (id, bike, distance, name, moving_time, elapsed_time, elev, type, avg_speed, max_speed, calories, rider) values (?,?,?,?,?,?,?,?,?,?,?,?)', a_list)

    def initialize_rider(self, rider_values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('insert into riders (name, dob, weight, fthr) values (?, ?, ?, ?)',
                         rider_values)

    def add_part(self, part_values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('insert into parts (type, purchased, brand, price, weight, size, model, bike, inuse) values (?, ?, ?, ?, ?, ?, ?, ?, True)', part_values)

    def replace_part(self, part_values, old_part=None):
        self.add_part(part_values)
        if old_part is not None:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('update parts set inuse = False where id=old_part')

    def add_maintenance(self, main_values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('insert into maintenance (part, work, date) values (?, ?, ?)', main_values)

    def get_from_db(self, query):
        # execute the command
        with sqlite3.connect(self.db_path) as conn:
            res = pd.read_sql_query(query, conn)
        return res
            
    def get_all_ride_data(self, rider_id):
        query = "select * from rides where rider=%s" % rider_id
        with sqlite3.connect(self.db_path) as conn:
            self.all_rides = pd.read_sql_query(query, conn)
            
    def update_rider(self, rider_id):
        # want to calculate max and avg speeds
        self.get_all_ride_data(rider_id)
        ms = self.all_rides['max_speed'].max()
        av = self.all_rides['avg_speed'].max()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('update riders set max_speed = ?, avg_speed = ? where name = ?', (ms, av, rider_id))

    def update_bike(self, bike):
        query = 'select distance, elev from rides where bike=%s' %bike
        r = get_from_db(query)
        dist = r['distance'].sum()
        elev = r['elev'].sum()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('update bikes set total_mi = ?, total_elev = ? where name=?', (dist, elev, bike))

    def get_maintenance_logs(self, part=None, bike=None, date=None):
        # get the maintenance record for a part or bike
        if part is not None:
            if date is not None:
                query = "select * from parts where part=%s and date>=%s" %(part, date)
            else:
                query = "select * from parts where part=%s" %part
        else if bike is not None:
            if date is not None:
                query = "select * from parts where bike=%s and date>=%s" %(bike, date)
            else:
                query = "select * from parts where bike=%s" %bike
        else if date is not None:
            query = "select * from parts where date >= %s" %date
        with sqlite3.connect(self.db_path) as conn:
            self.maintenance = pd.read_sql_query(query, conn)

    def calculate_totals(self, bike):
        # calculate some summary stats for a given bike
        q1 = "select * from parts where bike=%s" %bike
        q2 = "select * from maintenance where bike=%s" %bike
        q3 = "select distance, elev, moving_time, elapsed_time from rides where bike=%s"

    def add_bike(self, bike_values):
        # add a new bike manually
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('insert into bikes (id, name, color, purchased, price, rider) values (?, ?, ?, ?, ?, ?)' bike_values)

    def auto_add_bikes(self):
        with sqlite3.connect(self.db_path) as conn:
            bike_list = pd.read_sql_query('select distinct bike from rides', conn)
            current_bike_list = pd.read_sql_query('select id from bikes', conn)
            new_bikes = [x for x in bike_list not in current_bike_list]
            if len(new_bikes) > 0:
                for bike in new_bikes:
                    conn.execute('insert into bikes (id) values (?)', (bike))
        
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


# Try this out!
db = my_db(db_path)
db.strava_activity_to_db(activity)

# A full path:
db = my_db(db_path)
rider_name = "Brendan"
# test if the database exists and if not, initialize it
def initialize_db(db_path, rider_name, rider_dob, rider_weight, rider_fthr):
    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            with open(schema_path, 'rt') as f:
                schema = f.read()
            conn.executescript(schema)
    else:
        print("It appears that a database already exists there. No action taken.")
        return
    rider_info = (rider_name, rider_dob, rider_weight, rider_fthr)
    db.initialize_rider(rider_info)
    db.initialize_rides(all_activities, rider_name)
