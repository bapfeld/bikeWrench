###########################################
# Imports
###########################################

from stravalib.client import Client
from stravalib import unithelper
import configparser, argparse, sqlite3, os, sys, re, requests
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
        self.auto_add_bikes()

    def get_units(self):
        u = self.get_from_db('select units from riders')
        self.units = u['units'][0]

    def add_ride(self, ride_info):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT into rides (id, bike, distance, name, date, moving_time, elapsed_time, elev, type, avg_speed, max_speed, calories, rider) values (?,?,?,?,?,?,?,?,?,?,?,?,?)""", ride_info)

    def add_multiple_rides(self, activity_list, rider_name):
        def gear_try(x):
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
                conn.execute('UPDATE parts SET inuse = False WHERE id=?', (old_part, ))

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
        av = self.all_rides['avg_speed'].mean()
        tot = self.all_rides['distance'].sum()
        sql = """UPDATE riders 
                 SET max_speed = ?, avg_speed = ?, total_dist = ? 
                 WHERE name = ?"""
        self.edit_entry(sql, (ms, av, tot, rider_id))
        
    def update_bike(self, bike_name):
        try:
            bike_id = self.get_from_db("SELECT id from bikes WHERE name='%s'" %bike_name)
            bike_id = bike_id['id'][0]
            query = "SELECT distance, elev from rides WHERE bike='%s'" %bike_id
            r = self.get_from_db(query)
            dist = r['distance'].sum()
            elev = r['elev'].sum()
            sql = 'UPDATE bikes SET total_mi = ?, total_elev = ? WHERE name=?'
            self.edit_entry(sql, (dist, elev, bike_name))
        except:
            print("No bike found for that name")
        
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
            bike_list = list(bike_list['bike'])
            current_bike_list = list(current_bike_list['id'])
            new_bikes = [x for x in bike_list if x not in current_bike_list]
            if len(new_bikes) > 0:
                print('New bikes detected.')
                print('You can edit the bike info from the bike menu')
                print('New bike ids: %s' %', '.join(new_bikes))
                for bike in new_bikes:
                    conn.execute('INSERT into bikes (id) values (?)', (bike, ))

    def auto_get_bike_names(self, strava_object):
        self.get_all_bike_ids()
        sql = """UPDATE bikes 
                 SET (name) = (?) 
                 WHERE id = ?"""
        if self.all_bike_ids.shape[0] > 0:
            new_ids = list(self.all_bike_ids['id'][self.all_bike_ids['name'].isnull()])
            new_ids = [x for x in new_ids if x != 'Unknown']
            if len(new_ids) > 0:
                for bike in new_ids:
                    try:
                        b = strava_object.client.get_gear(bike)
                        nm = b.name
                    except:
                        nm = None
                    if nm is not None:
                        vals = (nm, bike)
                        with sqlite3.connect(self.db_path) as conn:
                            conn.execute(sql, vals)

    def get_rider_name(self):
        query = 'select name from riders'
        rider_name = self.get_from_db(query)
        rider_name = rider_name['name'][0]
        return rider_name

    def gen_ride_id(self):
        self.get_all_ride_ids(self.rider_id)
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

    def test_conn(self):
        try:
            _ = requests.get('http://www.google.com', timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def fetch_new_activities(self):
        if self.test_conn():
            self.gen_secrets()
            activity_list = self.client.get_activities()
            if self.id_list is not None:
                self.new_id_list = [str(x.id) for x in activity_list if str(x.id) not in self.id_list and x.type == "Ride"]
            else:
                self.new_id_list = [x.id for x in activity_list]
            if len(self.new_id_list) > 0:
                self.new_activities = [self.client.get_activity(id) for id in self.new_id_list]
            else:
                self.new_activities = None
        else:
            print("No internet connection. Unable to update rides.")
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
def int_input_func(prompt, list_options=None):
    test_val = True
    while test_val:
        try:
            i = int(input(prompt))
            if list_options is not None:
                if i not in list_options:
                    raise KeyError()
            test_val = False
        except ValueError:
            print("You must enter an integer value")
        except KeyError:
            print("You must enter a value from the list")
    return i

def float_input_func(prompt):
    test_val = True
    while test_val:
        try:
            i = float(input(prompt))
            test_val = False
        except:
            print("You must enter a numeric value")
    return i

def str_input_func(prompt, list_options=None):
    test_val = True
    while test_val:
        try:
            i = input(prompt)
            if i == '':
                raise ValueError()
            if list_options is not None:
                if i not in list_options:
                    raise KeyError()
            test_val = False
        except ValueError:
            print("You must enter a value")
        except KeyError:
            print("You must enter a value from the list")
    return i

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
    os.system('clear')
    print('Actions: ')
    print('(1): Get new rides')
    print('(2): Rider actions')
    print('(3): Bike actions')
    print('(4): Parts actions')
    print('(5): Ride actions')
    print('(6): Exit')

def show_rider_menu():
    os.system('clear')
    print('Rider actions: ')
    print('(1): Update rider stats')
    print('(2): Edit rider name')
    print('(3): Return to main menu')

def show_bike_menu():
    os.system('clear')
    print('Bike menu: ')
    print('(1): Update bike stats')
    print('(2): Edit bike')
    print('(3): Add new bike')
    print('(4): Automatically get bike names from Strava')
    print('(5): Return to main menu')

def show_parts_menu():
    # os.system('clear')
    print('Parts actions: ')
    print('(1): Get individual part stats')
    print('(2): Get all parts stats')
    print('(3): Maintain part')
    print('(4): Replace part')
    print('(5): Add part')
    print('(6): Return to main menu')

def show_ride_menu():
    os.system('clear')
    print('Ride actions: ')
    print('(1): Add manual ride')
    print('(2): Return to main menu')

def startup(db_path, schema, rider_name):
    db = my_db(db_path, rider_name)
    db_is_new = not os.path.exists(db_path)
    if db_is_new:
        print("Initializing a new database for %s" %rider_name)
        preferred_units = str_input_func('Imperial (i) or Metric (m)?: ',
                                         list_options=['i', 'm'])
        if preferred_units == "i":
            preferred_units = "imperial"
        else:
            preferred_units = "metric"
        create_db(db_path, schema)
        db.initialize_rider(preferred_units)
    db.secondary_init()
    return db

def part_summary_func(db, switch, b, p, u):
    # start by getting the bike id based on the name
    db.get_all_bike_ids()
    bikes = db.all_bike_ids
    bid = bikes.loc[bikes['name'] == b, :]['id'].values[0]
    if switch == "a":
        q = """SELECT distance, elapsed_time, elev 
               FROM rides
               WHERE bike = '%s'
               AND date >= (SELECT purchased 
                            FROM parts
                            WHERE id = %i)""" %(bid, p)
        pt = db.get_from_db(q)
        mrld = "purchase date"
    elif switch == "l":
        q = """SELECT * from maintenance
               WHERE id = %i""" %p
        logs = db.get_from_db(q)
        if logs.shape[0] > 0:
            mrld = logs['date'].max()
        else:
            print("No maintenance logs found for %s. Setting date to Jan 1, 1900" %p)
            mrld = '1900-01-01'
        q2 = """SELECT distance, elapsed_time, elev from rides
                WHERE bike = '%s'
                AND date >= date(%s)""" % (bid, mrld)
        pt = db.get_from_db(q2)
    elif switch == "d":
        dt = str_input_func("Date (YYYY-MM-DD): ")
        # need to generate some dates here
        # this is where i left off
        q = """SELECT distance, elapsed_time, elev from rides 
               WHERE bike = '%s' 
               AND date >= date(%s)""" % (bid, dt)
        pt = db.get_from_db(q)
    dist = pt['distance'].sum()
    time = pt['elapsed_time'].sum()
    elev = pt['elev'].sum()
    print("Since %s" %(str(mrld)))
    if u == "imperial":
        print("Total distance: %.1f miles" %dist)
        print("Total time: %.1f hours" %time)
        print("Total elevation: %.0f feet" %elev)
    else:
        print("Total distance: %.1f kilometers" %dist)
        print("Total time: %.1f hours" %time)
        print("Total elevation: %.0f meters" %elev)

def bike_list_func(db):
    db.get_all_bike_ids()
    blist = list(db.all_bike_ids['name'])
    blist_clean = [x for x in blist if x is not None]
    if len(blist_clean) < len(blist):
        print("NOTE: Not all bikes in database have a name. These will not appear in the list below.")    
    return blist_clean

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
    u = db.units
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
                if u == 'imperial':
                    print('Global Max Speed: %.2f mph' %rd['max_speed'])
                    print('Global Average Speed: %.2f mph' %rd['avg_speed'])
                    print('Global Total Distance: %.1f miles' %rd['total_dist'])
                else:
                    print('Global Max Speed: %.2f kph' %rd['max_speed'])
                    print('Global Average Speed: %.2 kph' %rd['avg_speed'])
                    print('Global Total Distance: %.1f kilometers' %rd['total_dist'])
                input("Press enter to continue")
            elif subselection == 2:
                # edit rider
                rd = db.get_from_db('select * from riders')
                rd = rd.to_dict('records')[0]
                print("Current rider info: ")
                print("Name: ", rd['name'])
                print("Preferred units: ", rd['units'])
                nm = str_input_func("New name: ")
                db.edit_entry("""UPDATE riders 
                                 SET name = ?
                                 WHERE name = ?""",
                              (nm, rider_name))
            elif subselection == 3:
                # return to main menu
                pass
        elif selection == 3:
            # Bike actions
            blist = bike_list_func(db)
            if len(blist) == 0:
                print("No bikes found in database. Try updating bike lists first.")
                pass
            show_bike_menu()
            subselection_function(list(range(1, 6)))
            if subselection == 1:
                # update bike stats
                print('Current list of bikes in database: ', ', '.join(blist))
                b = str_input_func("Name of bike to update: ",
                                   list_options=blist)
                db.update_bike(b)
                # show the results from the update
                q = "SELECT * from bikes WHERE name = '%s'" %b
                bk = db.get_from_db(q)
                bk = bk.to_dict('records')[0]
                print("Name: ", bk['name'])
                if u == "imperial":
                    print("Total Distance Ridden: %.2f miles" %bk['total_mi'])
                    print("Total Elevation Climbed: %.0f feet" %bk['total_elev'])
                else:
                    print("Total Distance Ridden: %.2f kilometers" %bk['total_mi'])
                    print("Total Elevation Climbed: %.0f meters" %bk['total_elev'])
                input("Press enter to continue")
            elif subselection == 2:
                # edit bike
                print('Current list of bikes in database: ', ' '.join(blist))
                b = str_input_func("Name of bike to edit: ",
                                   list_options=blist)
                # report current bike info
                q = "SELECT * from bikes WHERE name = '%s'" %b
                bk = db.get_from_db(q)
                bk = bk.to_dict('records')[0]
                print("Name: ", bk['name'])
                print("Color: ", bk['color'])
                print("Purchased: ", bk['purchased'])
                print("Price: ", bk['price'])
                # ask for new info
                nm = input("New bike name (leave blank to leave unchanged): ")
                if nm == '':
                    nm = bk['name']
                cl = input("New color (leave blank to leave unchanged): ")
                if cl == '':
                    cl = bk['color']
                pur = input("New purchase date (leave blank to leave unchanged): ")
                if pur == '':
                    pur = bk['purchased']
                pr = input("New price (leave blank to leave unchanged): ")
                if pr == '':
                    pr = bk['price']
                else:
                    pr = float(pr)
                db.edit_entry("""UPDATE bikes 
                                 SET name = ?, color = ?, purchased = ?, price = ? 
                                 WHERE name = ?""",
                              (nm, cl, pur, pr, b))
            elif subselection == 3:
                # Add a new bike
                b = str_input_func("Name of new bike: ")
                c = str_input_func("Color of new bike: ")
                p = str_input_func("Purchase date of new bike: ")
                pr = str_input_func("Price of new bike: ")
                i = str_input_func("Strava identifier of new bike: ")
                db.add_bike((i, b, c, p, pr))
            elif subselection == 4:
                # automatically get the bike names from strava
                db.auto_get_bike_names(st)
            elif subselection == 5:
                # exit to main menu
                pass
        elif selection == 4:
            # Parts actions
            # first, show bike list and ask which bike to list parts for
            blist = bike_list_func(db)
            if len(blist) == 0:
                print("No bikes found in database. Try updating bike lists first.")
                pass
            print('Current list of bikes in database: ', ' '.join(blist))
            all_list = blist.append('all')
            b = str_input_func("Which bike do you want to see parts for? Enter 'all' for all bike parts: ",
                               list_options=all_list)
            inuse = str_input_func("Do you want to see all bike parts (a) or only those current in use (c)? ",
                                   list_options=['a', 'c'])
            if b == 'all':
                if inuse == "a":
                    parts = db.get_from_db('SELECT * from parts')
                else:
                    parts = db.get_from_db('SELECT * from parts WHERE inuse=True')
            else:
                if inuse == "a":
                    q = "SELECT * from parts WHERE bike = '%s'" %b
                    parts = db.get_from_db(q)
                else:
                    q = "SELECT * from parts WHERE bike='%s' AND inuse=True" %b
                    parts = db.get_from_db(q)
            if parts.shape[0] == 0:
                print("No parts found")
                input("Press enter to continue")
            else:
                print("The following parts meet your search: ")
                for index, row in parts.iterrows():
                    print(row['id'], ": ", row['type'])
                print("\n")
            
            show_parts_menu()
            subselection_function(list(range(1, 7)))
            if subselection == 1:
                # get part stats
                p = int_input_func("Part id: ", list_options=list(parts['id']))
                b = parts.loc[parts['id'] == p, :]['bike'].iloc[0]
                switch = str_input_func("Do you want all (a) stats, everything since last maintenance (l), or from some arbitrary date (d)? ",
                                        list_options=['a', 'l', 'd'])
                part_summary_func(db, switch, b, p, u)
                input("Press enter to continue")
            elif subselection == 2:
                # get all parts stats
                b = str_input_func("Which bike do you want to see records for? ",
                                   list_options=blist)
                switch = str_input_func("Do you want all (a) stats, everything since last maintenance (l), or from some arbitrary date (d)? ",
                                        list_options=['a', 'l', 'd'])
                q = "SELECT id from parts WHERE bike = '%s'" %b
                all_parts = db.get_from_db(q)
                if all_parts.shape[0] > 0:
                    for index, row in all_parts.itertuples(index=False):
                        part_summary_func(db, switch, b, row['id'], u)
                    input("Press enter to continue")
            elif subselection == 3:
                # maintain parts
                part_id = int_input_func("Part id: ",
                                         list_options=list(parts['id']))
                work = str_input_func("Work performed: ")
                d = str_input_func("Date work performed (YYYY-MM-DD): ")
                db.add_maintenance((part_id, work, d))
            elif subselection == 4:
                # replace parts
                old_part_id = int_input_func("Part id: ",
                                             list_options=list(parts['id']))
                new_part = str_input_func("New part type: ")
                br = str_input_func("Brand: ")
                model = str_input_func("Model: ")
                pr = float_input_func("Price: ")
                wt = float_input_func("Weight (g): ")
                size = str_input_func("Size: ")
                bike = str_input_func("Which bike? ")
                pur = str_input_func("Date added (YYYY-MM-DD): ")
                db.replace_part((new_part, pur, br, pr, wt, size, model, bike), old_part_id)
            elif subselection == 5:
                # add new
                new_part = str_input_func("New part type: ")
                br = str_input_func("Brand: ")
                model = str_input_func("Model: ")
                pr = float_input_func("Price: ")
                wt = float_input_func("Weight (g): ")
                size = str_input_func("Size: ")
                bike = str_input_func("Which bike? ")
                pur = str_input_func("Date added (YYYY-MM-DD): ")
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
                bike = str_input_func('Bike used: ')
                distance = int_input_func('Distance: ')
                name = str_input_func('Ride name: ')
                date = str_input_func('Ride date (YYYY-MM-DD): ')
                moving_time = float_input_func('Moving time: ')
                elapsed_time = float_input_func('Elapsed time: ')
                elev = float_input_func('Elevation gain: ')
                ride_type = str_input_func('Ride type: ')
                avg_speed = distance / moving_time
                max_speed = 0
                calories = 0
                ride_info = (ride_id, bike, distance, name, date, moving_time, elapsed_time, elev, ride_type, avg_speed, max_speed, calories, rider_name)
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
