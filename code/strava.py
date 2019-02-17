###########################################
# Imports
###########################################

from stravalib.client import Client
import configparser
import sqlite3
import os, sys, re
import pandas as pd

###########################################
# Database Class
###########################################
class my_db():
    """Class to operate on a database

    """
    def __init__(self, db_path, rider_id):
        self.db_path = db_path
        self.get_all_ride_ids(rider_id)

    def add_ride(self, ride_info):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT into rides (id, bike, distance, name, moving_time, elapsed_time, elev, type, avg_speed, max_speed, calories, rider) values (?,?,?,?,?,?,?,?,?,?,?,?)', ride_info)

    def add_multiple_rides(self, activity_list, rider_name):
        def gear_try(x):
            try:
                out = x.gear.id
            except AttributeError:
                out = 'Unknown'
            return out
        a_list = [(a.id, gear_try(a), float(a.distance), a.name, a.moving_time.seconds, a.elapsed_time.seconds, float(a.total_elevation_gain), a.type, float(a.average_speed), float(a.max_speed), float(a.calories), rider_name, ) for a in activity_list]
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany('INSERT into rides (id, bike, distance, name, moving_time, elapsed_time, elev, type, avg_speed, max_speed, calories, rider) values (?,?,?,?,?,?,?,?,?,?,?,?)', a_list)

    def initialize_rider(self, rider_values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT into riders (name, dob, weight, fthr) values (?, ?, ?, ?)',
                         rider_values)

    def add_part(self, part_values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT into parts (type, purchased, brand, price, weight, size, model, bike, inuse) values (?, ?, ?, ?, ?, ?, ?, ?, True)', part_values)

    def replace_part(self, part_values, old_part=None):
        self.add_part(part_values)
        if old_part is not None:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('UPDATE parts SET inuse = False WHERE id=?', (old_part))

    def add_maintenance(self, main_values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT into maintenance (part, work, date) values (?, ?, ?)', main_values)

    def get_from_db(self, query):
        with sqlite3.connect(self.db_path) as conn:
            res = pd.read_sql_query(query, conn)
        return res
    
    def edit_entry(self, sql, values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, values)
            
    def get_all_ride_data(self, rider_id):
        query = "SELECT * from rides WHERE rider='%s'" % rider_id
        with sqlite3.connect(self.db_path) as conn:
            self.all_rides = pd.read_sql_query(query, conn)

    def get_all_ride_ids(self, rider_id):
        query = "SELECT id from rides WHERE rider='%s'" % rider_id
        self.all_ride_ids = self.get_from_db(query)

    def get_all_bike_ids(self):
        query = "SELECT id, name from bikes"
        self.all_bike_ids = self.get_from_db(query)
            
    def update_rider(self, rider_id):
        # want to calculate max and avg speeds
        self.get_all_ride_data(rider_id)
        ms = self.all_rides['max_speed'].max()
        av = self.all_rides['avg_speed'].max()
        tot = self.all_rides['distance'].sum()
        sql = 'UPDATE riders SET max_speed = ?, avg_speed = ?, total_dist = ? WHERE name = ?'
        self.edit_entry(sql, (ms, av, tot, rider_id))
        
    def update_bike(self, bike):
        query = "SELECT distance, elev from rides WHERE bike='%s'" %bike
        r = self.get_from_db(query)
        dist = r['distance'].sum()
        elev = r['elev'].sum()
        sql = 'UPDATE bikes SET total_mi = ?, total_elev = ? WHERE name=?'
        self.edit_entry(sql, (dist, elev, bike))
        
    def get_maintenance_logs(self, part=None, bike=None, date=None):
        # get the maintenance record for a part or bike
        if part is not None:
            if date is not None:
                query = "SELECT * from parts WHERE part='%s' AND date>='%s'" %(part, date)
            else:
                query = "SELECT * from parts WHERE part='%s'" %part
        elif bike is not None:
            if date is not None:
                query = "SELECT * from parts WHERE bike='%s' AND date>='%s'" %(bike, date)
            else:
                query = "SELECT * from parts WHERE bike='%s'" %bike
        elif date is not None:
            query = "SELECT * from parts WHERE date >= '%s'" %date
        self.maintenance = self.get_from_db(query)

    def calculate_totals(self, bike):
        # calculate some summary stats for a given bike
        q1 = "SELECT * from parts WHERE bike='%s'" %bike
        q2 = "SELECT * from maintenance WHERE bike='%s'" %bike
        q3 = "SELECT distance, elev, moving_time, elapsed_time from rides WHERE bike='%s'"

    def add_bike(self, bike_values):
        # add a new bike manually
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT into bikes (id, name, color, purchased, price, rider) values (?, ?, ?, ?, ?, ?)', bike_values)

    def auto_add_bikes(self):
        with sqlite3.connect(self.db_path) as conn:
            bike_list = pd.read_sql_query('SELECT distinct bike from rides', conn)
            current_bike_list = pd.read_sql_query('SELECT id from bikes', conn)
            new_bikes = [x for x in bike_list not in current_bike_list]
            if len(new_bikes) > 0:
                for bike in new_bikes:
                    conn.execute('INSERT into bikes (id) values (?)', (bike))

    def get_rider_name(self):
        query = 'select name from riders'
        rider_name = self.get_from_db(query)
        rider_name = rider_name['name']

    def gen_ride_id(self):
        self.get_all_ride_ids()
        ride_ids = [str(x) for x in self.all_ride_ids]
        ride_ids = '--'.join(ride_ids)
        ids = re.findall(r'(?:^|-)(\d{1,3})(?:-|$)', ride_ids)
        if len(ids) > 0:
            ids = [int(x) for x in ids]
            new_id = max(ids) + 1
            return new_id
        else:
            return 1
        
###########################################
# Strava class
###########################################

class strava():
    """Class to connect to strava using stravalib and update ride data. Inherits from stravalib.client.Client

    """
    def __init__(self, stravalib_client, id_list, ini_path):
        self.id_list = id_list
        self.ini_path = ini_path
        self.client = stravalib_client
        self.gen_secrets()

    def gen_secrets(self):
        config = configparser.ConfigParser()
        config.read(self.ini_path)
        code = config['Strava']['code']
        token_response = self.client.exchange_code_for_token(client_id=10185,
                                                        client_secret=config['Strava']['client_secret'],
                                                        code=code)
        self.client.access_token = token_response['access_token']
        self.client.refresh_token = token_response['refresh_token']
        self.client.expires_at = token_response['expires_at']

    def fetch_new_activities(self):
        activity_list = self.client.get_activities()
        if self.id_list is not None:
            self.new_id_list = [x.id for x in activity_list if x.id not in self.id_list]
        else:
            self.new_id_list = [x.id for x in activity_list]
        if len(self.new_id_list) > 0:
            self.new_activities = [self.client.get_activity(id) for id in self.new_id_list]
        else:
            self.new_activities = None

###########################################
# Create the database
###########################################
def create_db(db_path, schema_path, rider_name, rider_dob, rider_weight, rider_fthr):
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, 'rt') as f:
            schema = f.read()
        conn.executescript(schema)
    rider_info = (rider_name, rider_dob, rider_weight, rider_fthr)
    db.initialize_rider(rider_info)

###########################################
# Main interaction functions
###########################################
def selection_function(list_options):
    while True:
        try:
            global selection
            selection = int(input('Make a selection: '))
            if selection not in list_options:
                raise ValueError()
            break
        except ValueError:
            print("Invalid selection. You must enter an integer from the menu list")
    return

def subselection_function(list_options):
    while True:
        try:
            global subselection
            subselection = int(input('Make a selection: '))
            if subselection not in list_options:
                raise ValueError()
            break
        except ValueError:
            print("Invalid selection. You must enter an integer from the menu list")
    return

def show_main_menu():
    print('Actions: ')
    print('(1): Get new rides')
    print('(2): Rider actions')
    print('(3): Bike actions')
    print('(4): Parts actions')
    print('(5): Ride actions')
    print('(6): Exit')

def show_rider_menu():
    print('Rider actions: ')
    print('(1): Update rider stats')
    print('(2): Edit rider')
    print('(3): Return to main menu')

def show_bike_menu():
    print('Bike menu: ')
    print('(1): Update bike stats')
    print('(2): Edit bike')
    print('(3): Return to main menu')

def show_parts_menu():
    print('Parts actions: ')
    print('(1): Get individual part stats')
    print('(2): Get all parts stats')
    print('(3): Maintain part')
    print('(4): Replace part')
    print('(5): Return to main menu')

def show_ride_menu():
    print('Ride actions: ')
    print('(1): Add manual ride')
    print('(2): Return to main menu')

def startup(db_path, schema_path):
    db_is_new = not os.path.exists(db_path)
    if db_is_new:
        print("Initializing a new database")
        rider_name = input('Rider name: ')
        rider_dob = input('Rider DOB: ')
        rider_weight = input('Rider weight: ')
        rider_fthr = input('Rider Functional Threshold Heart Rate: ')
        create_db(db_path, schema_path, rider_name, rider_dob, rider_weight, rider_fthr)


###########################################
# Main
###########################################

def main():
    # Initialize everything
    startup(db_path, schema_path)
    db = my_db(db_path, rider_name)
    cl = Client()
    st = strava(cl, db.all_ride_ids['id'], ini_path) # need to define ini_path somewhere
    while True:
        # Fetch rider name
        rider_name = db.get_rider_name()
        show_main_menu()
        selection_function(list(range(1, 7)))
        # take action based on input
        if selection == 1:
            # Option 1: update rides from strava
            # Update the ride database
            st.fetch_new_activities()
            if st.new_activities is not None:
                db.add_multiple_rides(st.new_activities, rider_name)
        elif selection == 2:
            # Rider actions
            show_rider_menu()
            subselection_function(list(range(1, 4)))
            if subselection == 1:
                # update rider stats
                db.update_rider(rider_name)
                print("New Rider Info: ")
                rd = db.get_from_db('select * from riders')
                rd = rd.to_dict('records')[0]
                print('Name: ', rd['name'])
                print('Global Max Speed: ', rd['max_speed'])
                print('Global Average Speed: ', rd['avg_speed'])
                print('Global Total Distance: ', rd['total_dist'])
            elif subselection == 2:
                # edit rider
                rd = db.get_from_db('select * from riders')
                rd = rd.to_dict('records')[0]
                print("Current rider info: ")
                print("Name: ", rd['name'])
                print("DOB: ", rd['dob'])
                print("Weight: ", rd['weight'])
                print("Functional Threshold Heart Rate: ", rd['fthr'])
                nm = input("New name: ")
                if nm == '':
                    nm = rd['name']
                dob = input("New DOB: ")
                if dob == '':
                    dob = rd['dob']
                wt = input("New weight: ")
                if wt == '':
                    wt = rd['weight']
                hr = input("New Functional Threshold Heart Rate: ")
                if hr == '':
                    hr = rd['fthr']
                db.edit_entry('UPDATE riders SET name = ?, dob = ?, weight = ?, fthr = ? WHERE name = ?', (nm, dob, wt, fthr, rider_name))
            elif subselection == 3:
                # return to main menu
                pass
        elif selection == 3:
            # Bike actions
            show_bike_menu()
            subselection_function(list(range(1, 4)))
            if subselection == 1:
                # update bike stats
                db.get_all_bike_ids()
                print('Current list of bikes in database: ', ' '.join(db.all_bike_ids['name']))
                b = input("Name of bike to update: ")
                db.update_bike(b)
                # show the results from the update
                bk = db.get_from_db('select * from bikes where name=?', (b))
                bk = rd.to_dict('records')[0]
                print("Name: ", bk['name'])
                print("Total Distance Ridden: ", bk['total_mi'])
                print("Total Elevation Climbed: ", bk['total_elev'])
            elif subselection == 2:
                # edit bike
                db.get_all_bike_ids()
                print('Current list of bikes in database: ', ' '.join(db.all_bike_ids['name']))
                b = input("Name of bike to edit: ")
                # report current bike info
                bk = db.get_from_db('select * from bikes where name=?', (b))
                bk = rd.to_dict('records')[0]
                print("Name: ", bk['name'])
                print("Color: ", bk['color'])
                print("Purchased: ", bk['purchased'])
                print("Price: ", bk['price'])
                # ask for new info
                nm = input("New bike name: ")
                if nm == '':
                    nm = bk['name']
                cl = input("New color: ")
                if cl == '':
                    cl = bk['color']
                pur = input("New purchase date: ")
                if pur == '':
                    pur = bk['purchased']
                pr = float(input("New price: "))
                if pr == '':
                    pr = bk['price']
                db.edit_entry('UPDATE bikes SET name = ?, color = ?, purchased = ?, price = ? WHERE name = ?', (nm, cl, pur, pr, b))
                # run an update function
            elif subselection == 3:
                # exit to main menu
                pass
        elif selection == 4:
            # Parts actions
            # first, show bike list and ask which bike to list parts for
            db.get_all_bike_ids()
            print('Current list of bikes in database: ', ' '.join(db.all_bike_ids['name']))
            b = input("Which bike do you want to see parts for? Enter 'all' for all bike parts: ")
            u = input("Do you want to see all bike parts (a) or only those current in use (c)?")
            if b == 'all':
                if u == "a":
                    parts = db.get_from_db('SELECT * from parts')
                else:
                    parts = db.get_from_db('SELECT * from parts WHERE inuse=True')
            else:
                if u == "a":
                    parts = db.get_from_db('SELECT * from parts WHERE bike = ?', (b))
                else:
                    parts = db.get_from_db('SELECT * from parts WHERE bike=? AND inuse=True', (b))
            if parts.shape[0] == 0:
                print("No parts found")
            else:
                print("The following parts meet your search: ")
                for index, row in parts.iterrows():
                    print(row['id'], ": ", row['type'])
            
            show_parts_menu()
            subselection_function(list(range(1, 6)))
            if subselection == 1:
                # get part stats
                p = int(input("Part id: "))
                b = parts['bike'].where(id == p)
                # need to generate some dates here
                # this is where i left off
                pt = db.get_from_db('SELECT distance, elapsed_time, elev from rides WHERE bike=? AND date IN ?', (b, dates))
            elif subselection == 2:
                # get all parts stats
                pass
            elif subselection == 3:
                # maintain parts
                pass
            elif subselection == 4:
                # replace parts
                pass
            elif subselection == 5:
                # return to main menu
                pass
        elif selection == 5:
            # Ride options
            show_ride_menu()
            subselection_function(list(range(1, 3)))
            if subselection == 1:
                print("Adding a new manual entry. Input required.")
                ride_id = db.gen_ride_id()
                bike = input('Bike used: ')
                distance = int(input('Distance: '))
                name = input('Ride name: ')
                moving_time = float(input('Moving time: '))
                elapsed_time = float(input('Elapsed time: '))
                elev = float(input('Elevation gain: '))
                ride_type = input('Ride type: ')
                avg_speed = distance / moving_time
                max_speed = 0
                calories = 0
                ride_info = (ride_id, bike, distance, name, moving_time, elapsed_time, elev, ride_type, avg_speed, max_speed, calories, rider_name)
                db.add_ride(ride_info)
            elif subselection == 2:
                # return to the main menu
                pass
        elif selection == 6:
            # exit option
            break
    

###########################################
# Temporary values
###########################################
# Let's start by building up a temporary database
db_file = 'strava.db'
db_path = os.path.expanduser('~/strava/data/' + db_file)
schema_file = 'create_db.sql'
schema_path = os.path.expanduser('~/strava/code/' + schema_file)
initial_rider_vals = ('Brendan', '6-6-88', '165', '190')
ini_path = os.path.expanduser('~/strava/code/strava.ini')
