import sqlite3
import datetime
import dateparser
from stravalib import unithelper


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
    else:
        max_speed = round(max_speed, 2)
        avg_speed = round(avg_speed, 2)
        tot_dist = round(tot_dist, 2)
        tot_climb = round(tot_climb, 2)
    return (max_speed, avg_speed, tot_dist, tot_climb)


def convert_summary_units(units, res):
    if units == 'imperial':
        try:
            dist = round(res[0] / 1.609, 2)
        except TypeError:
            dist = None
        try:
            climb = round(res[3] * 3.281, 2)
        except TypeError:
            climb = None
        try:
            mx_speed = round(res[6] / 1.609, 2)
        except TypeError:
            mx_speed = None
    else:
        try:
            dist = round(res[0], 2)
        except TypeError:
            dist = None
        try:
            climb = round(res[3], 2)
        except TypeError:
            climb = None
        try:
            mx_speed = round(res[6], 2)
        except TypeError:
            mx_speed = None
    try:
        mv_time = round(res[4], 1)
    except TypeError:
        mv_time = None
    try:
        s_time = round(res[5], 1)
    except TypeError:
        s_time = None
    try:
        cal = round(res[7], 2)
    except TypeError:
        cal = None
    return (dist, res[1], res[2], climb, mv_time, s_time, mx_speed, cal)


def combine_res(n_all, n_virt):
    return (round(n_all - n_virt, 1), n_virt, n_all)


def summary_stats_combo(r_all, r_virt, u):
    r_all = convert_summary_units(u, r_all)
    r_virt = convert_summary_units(u, r_virt)
    out = dict()
    out['dist'] = combine_res(r_all[0], r_virt[0])
    out['min_dt'] = min([r_all[1], r_virt[1]])
    out['max_dt'] = max([r_all[2], r_virt[2]])
    out['elev'] = combine_res(r_all[3], r_virt[3])
    out['moving_time'] = combine_res(r_all[4], r_virt[4])
    out['elapsed_time'] = combine_res(r_all[5], r_virt[5])
    out['max_speed'] = (r_all[6], r_virt[6])
    out['cal'] = combine_res(r_all[7], r_virt[7])
    return out


def update_rider(current_nm, nm, units, db_path):
    q = f"""UPDATE riders
            SET name = '{nm}',
                units = '{units}'
            WHERE name = '{current_nm}'"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(q)


def update_bike(b_id, nm, color, purchase, price, mfg, db_path):
    q = f"""UPDATE bikes
            SET name = '{nm}',
                color = '{color}',
                purchased = '{purchase}',
                price = '{price}',
                mfg = '{mfg}'
            WHERE bike_id = '{b_id}'"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(q)


def update_part(p_id, p_type, added, brand, price, weight,
                size, model, db_path):
    q = f"""UPDATE parts
            SET type = '{p_type}',
                added = '{added}',
                brand = '{brand}',
                price = '{price}',
                weight = '{weight}',
                size = '{size}',
                model = '{model}'
            WHERE part_id = '{p_id}'"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(q)


def get_all_bike_ids(db_path):
    query = "SELECT bike_id FROM bikes"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res = c.fetchall()
    all_bike_ids = [x[0] for x in res]
    return all_bike_ids


def get_all_bikes(db_path):
    query = "SELECT * FROM bikes;"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res = c.fetchall()
    return res


def get_bike_details(db_path, bike_id):
    query = f"SELECT * FROM bikes WHERE bike_id = '{bike_id}';"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res = c.fetchone()
    return res


def get_all_ride_ids(db_path):
    query = "SELECT ride_id FROM rides"
    max_dt_query = "SELECT MAX(date) FROM rides"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        id_list = [x[0] for x in c.fetchall()]
        if len(id_list) > 0:
            c.execute(max_dt_query)
            max_dt_res = c.fetchone()
            max_dt = dateparser.parse(max_dt_res[0])
            max_dt = max_dt - datetime.timedelta(days=1)
            max_dt = max_dt.strftime('%Y-%m-%d')
        else:
            max_dt = None
    return (id_list, max_dt)


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
                            bike)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", part_values)


def get_all_bike_parts(db_path, current_bike):
    query = f"""SELECT *
                FROM parts
                WHERE bike = '{current_bike}'
                AND retired IS NULL"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        current_bike_parts_list = c.fetchall()
    return current_bike_parts_list


def get_maintenance(db_path, part_ids):
    query = """SELECT *
                FROM maintenance
                WHERE part in (
            """
    for p in part_ids:
        query += f"'{p}', "
    query = query.strip(', ')
    query += ') ORDER BY date desc;'
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res = c.fetchall()
    return res


def get_all_ride_data(db_path):
    query = "SELECT * FROM rides'"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        all_rides = c.fetchall()
    return all_rides


def get_ride_data_for_bike(db_path, bike_id, units, start_date=None,
                           end_date=None):
    query = f"""SELECT
                    SUM(distance) AS dist,
                    MIN(date) AS earliest_ride,
                    MAX(date) AS recent_ride,
                    SUM(elev) AS climb,
                    SUM(moving_time) AS mov_saddle_time,
                    SUM(elapsed_time) AS saddle_time,
                    MAX(max_speed) AS max_speed,
                    SUM(calories) AS calories
                FROM rides
                WHERE bike = '{bike_id}'"""
    query_virt = query + " AND type = 'VirtualRide'"
    if start_date is not None:
        query += f" AND date >= '{start_date}'"
    if end_date is not None:
        query += f" AND date <= '{end_date}'"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res_all = c.fetchone()
        c.execute(query_virt)
        res_virt = c.fetchone()
    res_out = summary_stats_combo(res_all, res_virt, units)
    return res_out


def get_ride_data_for_part(db_path, bike_id, early_date, late_date, units):
    query = f"""SELECT
                    SUM(distance) AS dist,
                    MIN(date) AS earliest_ride,
                    MAX(date) AS recent_ride,
                    SUM(elev) AS climb,
                    SUM(moving_time) AS mov_saddle_time,
                    SUM(elapsed_time) AS saddle_time,
                    MAX(max_speed) AS max_speed,
                    SUM(calories) AS calories
                FROM rides
                WHERE bike = '{bike_id}'
                  AND date >= '{early_date}'
                  AND date <= '{late_date}'"""
    query_virt = query + " AND type = 'VirtualRide'"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res_all = c.fetchone()
        c.execute(query_virt)
        res_virt = c.fetchone()
    res_out = summary_stats_combo(res_all, res_virt, units)
    return res_out


def add_multiple_rides(db_path, activity_list):
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
               a.start_date.strftime("%Y-%m-%d"),
               a.moving_time.seconds / 3600,
               a.elapsed_time.seconds / 3600,
               unit_try(a.total_elevation_gain, 'short_dist'),
               a.type,
               unit_try(a.average_speed, 'speed'),
               unit_try(a.max_speed, 'speed'),
               float(a.calories), ) for a in activity_list]

    with sqlite3.connect(db_path) as conn:
        sql = """INSERT INTO rides
                 (ride_id, bike, distance, name, date, moving_time,
                  elapsed_time, elev, type, avg_speed, max_speed,
                  calories)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""
        conn.executemany(sql, a_list)


def add_new_bike(db_path, bike_id, bike_name, bike_color,
                 bike_purchase, bike_price, bike_mfg):
    q = """INSERT INTO bikes
               (bike_id, name, color, purchased, price, mfg)
           VALUES
               (?, ?, ?, ?, ?, ?)"""
    vals = (bike_id, bike_name, bike_color, bike_purchase, bike_price,
            bike_mfg)
    with sqlite3.connect(db_path) as conn:
        conn.execute(q, vals)
        conn.commit()


def add_maintenance(db_path, part_id, work, dt):
    q = """INSERT INTO maintenance
               (part, work, date)
           VALUES
               (?, ?, ?)"""
    vals = (part_id, work, dt)
    with sqlite3.connect(db_path) as conn:
        conn.execute(q, vals)
        conn.commit()


def find_new_bikes(db_path):
    """Simple function to determine if there are any bikes
       that haven't been added
     """

    # Check what bikes already exist
    all_bike_ids = get_all_bike_ids(db_path)

    # And see what bikes appear in rides
    with sqlite3.connect(db_path) as conn:
        q = """SELECT DISTINCT
                   bike
               FROM
                   rides;
            """
        c = conn.cursor()
        c.execute(q)
        res = c.fetchall()

    new_bikes = [x[0] for x in res if x[0] not in all_bike_ids]
    if len(new_bikes) > 0:
        b_list = [(b, f'tmp_nm_{b}') for b in new_bikes]
        with sqlite3.connect(db_path) as conn:
            q = """INSERT INTO bikes
                   (bike_id, name)
                   VALUES (?, ?);
                """
            c.executemany(q, b_list)


def get_part_details(db_path, part_id):
    q1 = f"SELECT * FROM parts WHERE part_id = {part_id}"
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(q1)
        res = c.fetchone()
        q2 = f"SELECT bike_id, name FROM bikes WHERE bike_id = '{res[8]}'"
        c.execute(q2)
        res_2 = c.fetchone()
        b_id, b_nm = res_2[0], res_2[1]
    return (res, b_id, b_nm)


def get_part_averages(db_path):
    q = f"""SELECT type, AVG(price), AVG(weight),
                   AVG(dist), AVG(elev), AVG(retired - added)
            FROM retired_parts
            GROUP BY 1
         """
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(q)
        averages = c.fetchmany()

    return averages


def retire(db_path, retired_part, date_retired):
    q1 = f"""UPDATE parts 
             SET retired = '{date_retired}'
             WHERE part_id = '{retired_part}'
          """
    q2 = f"""SELECT * FROM parts WHERE part_id = '{retired_part}'"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(q1)
        c.execute(q2)
        p = c.fetchone()
        q3 = f"""SELECT SUM(distance), SUM(elev)
                 FROM rides
                 WHERE bike = '{p[8]}'
                 AND date >= '{p[2]}'
                 AND date <= '{p[9]}'"""
        c.execute(q3)
        part_summary = c.fetchone()
        res_out = list(p) + list(part_summary)
        q4 = """INSERT INTO retired_parts
                    (part_id, type, added, brand, price, weight,
                     size, model, bike, retired, virtual, dist, elev)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
             """
        c.execute(q4, res_out)
