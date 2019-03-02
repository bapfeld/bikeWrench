###########################################
# Imports
###########################################

from stravalib.client import Client
from stravalib import unithelper
import configparser, argparse, sqlite3, os, sys, re
import pandas as pd

###########################################
# Database Class
###########################################
class my_db():
    """Class to operate on a database

    """
    def __init__(self, db_path, rider_id):
        self.db_path = db_path
        self.rider_id = rider_id

    def secondary_init(self):
        self.get_all_ride_ids(self.rider_id)
        self.get_units()

    def get_units(self):
        u = self.get_from_db('select units from riders')
        self.units = u['units'][0]

    def add_ride(self, ride_info):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT into rides (id, bike, distance, name, date, moving_time, elapsed_time, elev, type, avg_speed, max_speed, calories, rider) values (?,?,?,?,?,?,?,?,?,?,?,?,?)""", ride_info)

    def add_multiple_rides(self, activity_list, rider_name):
        def gear_try(self, x):
            try:
                out = x.gear.id
            except AttributeError:
                out = 'Unknown'
            return out
        if self.units == 'imperial':
            a_list = [(a.id, gear_try(a),
                       float(unithelper.miles(a.distance)),
                       a.name,
                       a.start_date.strftime("%Y-%M-%d"), 
                       a.moving_time.seconds / 3600,
                       a.elapsed_time.seconds / 3600,
                       float(unithelper.feet(a.total_elevation_gain)),
                       a.type,
                       float(unithelper.mph(a.average_speed)),
                       float(unithelper.mph(a.max_speed)),
                       float(a.calories),
                       rider_name, ) for a in activity_list]
        else:
            a_list = [(a.id, gear_try(a),
                       float(unithelper.kilometers(a.distance)),
                       a.name,
                       a.start_date.strftime("%Y-%M-%d"), 
                       a.moving_time.seconds / 3600,
                       a.elapsed_time.seconds / 3600,
                       float(unithelper.meters(a.total_elevation_gain)),
                       a.type,
                       float(unithelper.kph(a.average_speed)),
                       float(unithelper.kph(a.max_speed)),
                       float(a.calories),
                       rider_name, ) for a in activity_list]
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany('INSERT into rides (id, bike, distance, name, date, moving_time, elapsed_time, elev, type, avg_speed, max_speed, calories, rider) values (?,?,?,?,?,?,?,?,?,?,?,?,?)', a_list)

    def initialize_rider(self, units):
        rider_values = (self.rider_id, units)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT into riders (name, units) 
                            values (?, ?)""",
                         rider_values)

    def add_part(self, part_values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT into parts (
                                type, 
                                purchased, 
                                brand, 
                                price, 
                                weight, 
                                size, 
                                model, 
                                bike, 
                                inuse) 
                            values (?, ?, ?, ?, ?, ?, ?, ?, True)""", part_values)

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
            conn.execute('INSERT into bikes (id, name, color, purchased, price) values (?, ?, ?, ?, ?)', bike_values)

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
    def __init__(self, stravalib_client, id_list, secrets_path):
        self.id_list = [str(x) for x in id_list]
        self.secrets_path = secrets_path
        self.client = stravalib_client
        self.gen_secrets()

    def gen_secrets(self):
        if self.secrets_path.endswith(".ini"):
            config = configparser.ConfigParser()
            config.read(self.secrets_path)
            code = config['Strava']['code']
            client_secret = config['Strava']['client_secret']
            client_id = config['Strava']['client_id']
        elif self.secrets_path.endswith(".gpg"):
            code, client_secret, client_id = self.get_encrypted_secrets()
        token_response = self.client.exchange_code_for_token(client_id=client_id,
                                                        client_secret=client_secret,
                                                        code=code)
        self.client.access_token = token_response['access_token']
        self.client.refresh_token = token_response['refresh_token']
        self.client.expires_at = token_response['expires_at']

    def get_encrypted_secrets(self):
        secrets = os.popen("gpg -q --no-tty -d %s" %self.secrets_path).read()
        s = re.search("code (.*?) client_secret (.*?) client_id (.*?)\n", secrets)
        return (s.group(1), s.group(2), s.group(3))

    def fetch_new_activities(self):
        activity_list = self.client.get_activities()
        if self.id_list is not None:
            self.new_id_list = [str(x.id) for x in activity_list if str(x.id) not in self.id_list and x.type == "Ride"]
        else:
            self.new_id_list = [x.id for x in activity_list]
        if len(self.new_id_list) > 0:
            self.new_activities = [self.client.get_activity(id) for id in self.new_id_list]
        else:
            self.new_activities = None

###########################################
# Create the database
###########################################
def create_db(db_path, schema):
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)

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
    print('(3): Add new bike')
    print('(4): Return to main menu')

def show_parts_menu():
    print('Parts actions: ')
    print('(1): Get individual part stats')
    print('(2): Get all parts stats')
    print('(3): Maintain part')
    print('(4): Replace part')
    print('(5): Add part')
    print('(6): Return to main menu')

def show_ride_menu():
    print('Ride actions: ')
    print('(1): Add manual ride')
    print('(2): Return to main menu')

def startup(db_path, schema, rider_name):
    db = my_db(db_path, rider_name)
    db_is_new = not os.path.exists(db_path)
    if db_is_new:
        print("Initializing a new database for %s" %rider_name)
        preferred_units = input('Imperial (i) or Metric (m)?: ')
        if preferred_units == "i":
            preferred_units = "imperial"
        else:
            preferred_units = "metric"
        create_db(db_path, schema)
        db.initialize_rider(preferred_units)
    db.secondary_init()
    return db

def part_summary_func(switch, b, p):
    if switch == "a":
        pt = db.get_from_db("""SELECT distance, elapsed_time, elev 
                               FROM rides
                               WHERE bike = ? AND part = ?""", (b, p))
        mrld = "purchase date"
    elif switch == "l":
        logs = db.get_from_db("""SELECT * from maintenance
                                 WHERE id = ?""", (p))
        if logs.shape[0] > 0:
            mrld = logs['date'].max()
        else:
            print("No maintenance logs found for %s. Setting date to Jan 1, 1900" %p)
            mrld = '1900-01-01'
        pt = db.get_from_db("""SELECT distance, elapsed_time, elev from rides
                               WHERE bike = ?
                               AND id = ?
                               AND date >= date(?)""", (b, p, mrld))
    elif switch == "d":
        dt = input("Date (YYYY-MM-DD): ")
        # need to generate some dates here
        # this is where i left off
        pt = db.get_from_db("""SELECT distance, elapsed_time, elev from rides 
                               WHERE bike = ? 
                               AND id = ?
                               AND date >= date(?)""", (b, p, dt))
    dist = pt['distance'].sum()
    time = pt['elapsed_time'].sum()
    elev = pt['elev'].sum()
    print("Since %s" %(str(mrld)))
    print("Total distance: %f" %dist)
    print("Total time: %f" %time)
    print("Total elevation: %f" %elev)

###########################################
# Main
###########################################

def main():
    # Initialize everything
    args_parser = argparse.ArgumentParser()
    params = initialize_params(args_parser)
    db_path = os.path.expanduser(params.db_file)
    secrets_path = os.path.expanduser(params.secrets_path)
    rider_name = params.rider_name
    db = startup(db_path, strava_db_schema, rider_name)
    cl = Client()
    st = strava(cl, db.all_ride_ids['id'], secrets_path)
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
                print("Preferred units: ", rd['units'])
                nm = input("New name: ")
                if nm == '':
                    nm = rd['name']
                u = input("New preferred units: ")
                if u == '':
                    u = rd['units']
                db.edit_entry("""UPDATE riders 
                                 SET name = ?, units = ? 
                                 WHERE name = ?""",
                              (nm, u, rider_name))
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
                db.edit_entry("""UPDATE bikes 
                                 SET name = ?, color = ?, purchased = ?, price = ? 
                                 WHERE name = ?""",
                              (nm, cl, pur, pr, b))
            elif subselection == 3:
                # Add a new bike
                b = input("Name of new bike: ")
                c = input("Color of new bike: ")
                p = input("Purchase date of new bike: ")
                pr = input("Price of new bike: ")
                i = input("Strava identifier of new bike: ")
                db.add_bike((i, b, c, p, pr))
            elif subselection == 4:
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
                switch = input("Do you want all (a) stats, everything since last maintenance (l), or from some arbitrary date (d)? ")
                part_summary_func(switch, b, p)
            elif subselection == 2:
                # get all parts stats
                b = input("Which bike do you want to see records for? ")
                switch = input("Do you want all (a) stats, everything since last maintenance (l), or from some arbitrary date (d)? ")
                all_parts = db.get_from_db("SELECT id from parts WHERE bike = ?", (b))
                if all_parts.shape[0] > 0:
                    for index, row in all_parts.iterrows:
                        part_summary_func(switch, b, row['id'])
            elif subselection == 3:
                # maintain parts
                part_id = int(input("Part id: "))
                work = input("Work performed: ")
                d = input("Date work performed (YYYY-MM-DD): ")
                db.add_maintenance((part_id, work, d))
            elif subselection == 4:
                # replace parts
                old_part_id = input("Part id: ")
                if old_part_id == '':
                    old_part_id = None
                else:
                    old_part_id = int(old_part_id)
                new_part = input("New part type: ")
                br = input("Brand: ")
                pr = float(input("Price: "))
                wt = float(input("Weight (g): "))
                size = input("Size: ")
                model = input("Model: ")
                bike = input("Which bike? ")
                pur = input("Date added: ")
                db.replace_part((new_part, pur, br, pr, wt, size, model, bike), old_part_id)
            elif subselection == 5:
                # replace parts
                new_part = input("New part type: ")
                br = input("Brand: ")
                pr = float(input("Price: "))
                wt = float(input("Weight (g): "))
                size = input("Size: ")
                model = input("Model: ")
                bike = input("Which bike? ")
                pur = input("Date added: ")
                db.add_part((new_part, pur, br, pr, wt, size, model, bike))
            elif subselection == 6:
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
    
def initialize_params(args_parser):
    args_parser.add_argument(
        '--db_file',
        help='Path to a local database',
        required=True
    )
    args_parser.add_argument(
        '--rider_name',
        help='Name of the rider',
        required=True
    )
    args_parser.add_argument(
        '--secrets_path',
        help='Path to the local secrets file.',
        required=True
    )
    return args_parser.parse_args()

strava_db_schema = """
-- Riders are top level
create table riders (
    name       text primary key,
    max_speed  real,
    avg_speed  real,
    total_dist real,
    units      text
);

-- Bikes belong to riders
create table bikes (
    id          text primary key,
    name        text,
    color       text,
    purchased   date,
    price       real,
    total_mi    real,
    total_elev  real
);

-- Rides record data about a bike ride
create table rides (
    id           integer primary key,
    bike         text not null references bike(id),
    distance     integer,
    name         text,
    date         date,
    moving_time  integer,
    elapsed_time integer,
    elev         real,
    type         text,
    avg_speed    real,
    max_speed    real,
    calories     real,
    rider        text not null references rider(name)
);

-- Parts belong to bikes
create table parts (
    id           integer primary key autoincrement not null,
    type         text,
    purchased    date,
    brand        text,
    price        real,
    weight       real,
    size         text,
    model        text,
    bike         text not null references bikes(name),
    inuse        text
);

-- Maintenance tasks record things that happen to parts
create table maintenance (
    id           integer primary key autoincrement not null,
    part         integer not null references parts(id),
    work         text,
    date         date
);
"""


if __name__ == '__main__':
    main()

###########################################
# Temporary values
###########################################
# Let's start by building up a temporary database
db_file = 'strava.db'
db_path = os.path.expanduser('~/strava/data/' + db_file)
secrets_path = os.path.expanduser('~/strava/code/strava.ini')
