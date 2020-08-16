import sqlite3
import datetime
from stravalib import unithelper


def get_all_bike_ids(db_path):
    query = "SELECT bike_id, name FROM bikes"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res = c.fetchall()
    all_bike_ids = {x[0]: x[1] for x in res}
    return all_bike_ids


def get_all_ride_ids(db_path, rider_name):
    query = f"SELECT ride_id FROM rides WHERE rider='{rider_name}'"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        id_list = [x[0] for x in c.fetchall()]
    return id_list


def get_rider_info(db_path):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM riders')
        res = c.fetchone()
        rider_name = res[0]
        units = res[1]
        if res[2] is not None:
            refresh_token = res[2]
            expires_at = datetime.datetime.fromtimestamp(res[3])
        else:
            refresh_token = None
            expires_at = None
        try:
            c.execute('SELECT MAX(max_speed) FROM rides')
            max_speed = round(c.fetchone()[0], 2)
        except:
            max_speed = 0
        try:
            c.execute('SELECT AVG(avg_speed) FROM rides')
            avg_speed = round(c.fetchone()[0], 2)
        except:
            avg_speed = 0
        try:
            c.execute('SELECT SUM(distance) FROM rides')
            tot_dist = round(c.fetchone()[0], 2)
        except:
            tot_dist = 0
        try:
            c.execute('SELECT SUM(elev) FROM rides')
            tot_climb = round(c.fetchone()[0], 2)
        except:
            tot_climb = 0
    max_speed, avg_speed, tot_dist, tot_climb = convert_rider_info(units,
                                                                   max_speed,
                                                                   avg_speed,
                                                                   tot_dist,
                                                                   tot_climb)
    return (rider_name, units, refresh_token, expires_at,
            max_speed, avg_speed, tot_dist, tot_climb)


def convert_rider_info(units, max_speed, avg_speed, tot_dist, tot_climb):
    if units == 'imperial':
        max_speed = round(max_speed / 1.609, 2)
        avg_speed = round(avg_speed / 1.609, 2)
        tot_dist = round(tot_dist / 1.609, 2)
        tot_climb = round(tot_climb * 3.281, 2)
    return (max_speed, avg_speed, tot_dist, tot_climb)


def edit_entry(db_path, sql, values):
    with sqlite3.connect(db_path) as conn:
        conn.execute(sql, values)


def replace_part(old_part=None):
    """Function not yet implemented"""
    pass


def add_part(db_path, part_values):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""INSERT INTO parts (
                            type, 
                            purchased, 
                            brand, 
                            price, 
                            weight, 
                            size, 
                            model, 
                            bike, 
                            inuse) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", part_values)


def get_all_bike_parts(db_path, current_bike):
    query = f"""SELECT *
                FROM parts 
                WHERE bike = '{current_bike}'
                AND inuse = 'TRUE'"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        current_bike_parts_list = c.fetchall()
    return current_bike_parts_list


def get_all_ride_data(db_path, rider_name):
    query = f"SELECT * FROM rides WHERE rider='{rider_name}'"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        all_rides = c.fetchall()
    return all_rides


def update_part(db_path, current_bike, current_part):
    query = f"""SELECT distance, elapsed_time, elev
                FROM rides 
                WHERE bike=(SELECT bike_id FROM bikes WHERE name='{current_bike}')
                AND date >= (SELECT purchased 
                             FROM parts 
                             WHERE part_id={current_part})"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res = c.fetchall()
    try:
        dist = round(sum([x[0] for x in res]), 2)
        dist = f'{dist:n}'
    except:
        dist = None
    try:
        elev = round(sum([x[2] for x in res]), 2)
        elev = f'{elev:n}'
    except:
        elev = None
    try:
        time = round(sum([x[1] for x in res]), 2)
        time = f'{time:n}'
    except:
        time = None
    return (dist, elev, time)


def add_multiple_rides(db_path, rider_name, activity_list):
    def gear_try(x):
        try:
            out = x.gear.id
        except AttributeError:
            out = 'Unknown'
        return out
    def unit_try(num, t):
        if t == 'long_dist':
            return float(unithelper.kilometers(num))
        elif t == 'short_dist':
            return float(unithelper.meters(num))
        elif t == 'speed':
            return float(unithelper.kph(num))
    a_list = [(a.id,
               gear_try(a),
               unit_try(a.distance, 'long_dist'),
               a.name,
               a.start_date.strftime("%Y-%M-%d"),
               a.moving_time.seconds / 3600,
               a.elapsed_time.seconds / 3600,
               unit_try(a.total_elevation_gain, 'short_dist'),
               a.type,
               unit_try(a.average_speed, 'speed'),
               unit_try(a.max_speed, 'speed'),
               float(a.calories),
               rider_name, ) for a in activity_list]

    with sqlite3.connect(db_path) as conn:
        sql = """INSERT INTO rides 
                 (ride_id, bike, distance, name, date, moving_time,
                  elapsed_time, elev, type, avg_speed, max_speed,
                  calories, rider) 
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""" 
        conn.executemany(sql, a_list)


def add_new_bike(db_path, units, bike_id, bike_name, bike_color,
                 bike_purchase, bike_price):
    q = """INSERT INTO bikes
               (bike_id, name, color, purchased, price) 
           VALUES 
               (?, ?, ?, ?, ?)"""
    vals = (bike_id, bike_name, bike_color, bike_purchase, bike_price)
    with sqlite3.connect(self.db_path) as conn:
        conn.execute(q, vals)
        conn.commit()


def find_new_bikes(db_path):
    """Simple function to determine if there are any bikes that haven't been added"""

    # Check what bikes already exist
    all_bike_ids = get_all_bike_ids()

    # And see what bikes appear in rides
    with sqlite3.connect(db_path) as conn:
        q = """SELECT
                   bike,
                   SUM(distance),
                   SUM(elev),
                   MIN(date),
                   MAX(date)
               FROM 
                   rides
               GROUP BY
                   1;"""
        c = conn.cursor()
        c.execute(q)
        res = c.fetchall()
        # Make sure that unknown bike is always last
        res.sort(key=lambda tup: tup[0], reverse=True)

    bike_id_keys = list(all_bike_ids.keys())
    new_bikes = [x for x in res if x[0] not in list(all_bike_ids.keys())]
    return new_bikes