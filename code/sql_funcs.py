###########################################
# Imports
###########################################
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QInputDialog, QToolTip, QGroupBox, QPushButton, QGridLayout, QMessageBox, QLabel, QButtonGroup, QRadioButton, QComboBox, QCalendarWidget, QLineEdit)
from PyQt5.QtGui import QFont
from stravalib.client import Client
from stravalib import unithelper
import configparser, argparse, sqlite3, os, sys, re, requests, keyring, platform, locale, datetime, dateparser
from functools import partial
from collections import OrderedDict
from input_form_dialog import FormOptions, get_input
from base_class import add_method, StravaApp

@add_method(StravaApp)
def get_all_bike_ids(self):
    query = "SELECT bike_id, name FROM bikes"
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        res = c.fetchall()
    self.all_bike_ids = {x[0]: x[1] for x in res}
    if len(res) > 0:
        self.current_bike = list(self.all_bike_ids.values())[0]
        self.get_all_bike_parts()
        if len(self.current_bike_parts_list) > 0:
            self.current_part = self.current_bike_parts_list[0][0]
    else:
        self.current_part = None

@add_method(StravaApp)
def get_all_ride_ids(self):
    query = f"SELECT ride_id FROM rides WHERE rider='{self.rider_name}'"
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        self.id_list = [x[0] for x in c.fetchall()]

@add_method(StravaApp)
def get_rider_info(self):
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM riders')
        res = c.fetchone()
        self.rider_name = res[0]
        self.units = res[1]
        if res[2] is not None:
            self.client.refresh_token = res[2]
            self.client.expires_at = datetime.datetime.fromtimestamp(res[3])
        else:
            self.client.refresh_token = None
            self.client.expires_at = None
        try:
            c.execute('SELECT MAX(max_speed) FROM rides')
            self.max_speed = round(c.fetchone()[0], 2)
        except:
            self.max_speed = 0
        try:
            c.execute('SELECT AVG(avg_speed) FROM rides')
            self.avg_speed = round(c.fetchone()[0], 2)
        except:
            self.avg_speed = 0
        try:
            c.execute('SELECT SUM(distance) FROM rides')
            self.tot_dist = round(c.fetchone()[0], 2)
        except:
            self.tot_dist = 0
        try:
            c.execute('SELECT SUM(elev) FROM rides')
            self.tot_climb = round(c.fetchone()[0], 2)
        except:
            self.tot_climb = 0

@add_method(StravaApp)
def convert_rider_info(self):
    if self.units == 'imperial':
        self.max_speed = round(self.max_speed / 1.609, 2)
        self.avg_speed = round(self.avg_speed / 1.609, 2)
        self.tot_dist = round(self.tot_dist / 1.609, 2)
        self.tot_climb = round(self.tot_climb * 3.281, 2)

@add_method(StravaApp)
def edit_entry(self, sql, values):
    with sqlite3.connect(self.db_path) as conn:
        conn.execute(sql, values)

@add_method(StravaApp)
def replace_part(self, old_part=None):
    self.msg.setText('Function not yet implemented')
    #     with sqlite3.connect(self.db_path) as conn:
    #         conn.execute("UPDATE parts SET inuse = 'True' WHERE part_id=?",
    #                      (old_part, ))

@add_method(StravaApp)
def get_part_inputs(self, new=True):
    if new:
        part_class, _ = QInputDialog.getItem(self,
                                             'Part Type',
                                             'What type of part are you adding?',
                                             list(self.parts_dict.keys()),
                                             0,
                                             False)
        part_type, _ = QInputDialog.getItem(self,
                                            'Part Type',
                                            'What type of part are you adding?',
                                            self.parts_dict[part_class],
                                            0,
                                            False)
    purchased_dt, _ = QInputDialog.getText(self,
                                           'Purchase date',
                                           'When did you purchase this part?')
    purchased_dt = dateparser.parse(purchased_dt)
    brand, _ = QInputDialog.getText(self,
                                    'Brand',
                                    'Part brand')
    model, _ = QInputDialog.getText(self,
                                    'Model',
                                    'Part model')
    price, _ = QInputDialog.getText(self,
                                    'Purchase price',
                                    'Price')
    price = re.sub(r'\$', '', price)
    weight, _ = QInputDialog.getText(self,
                                     'Part weight',
                                     'What does the part weigh (g)?')
    weight = re.sub(r'\s*g', '', weight)
    sz, _ = QInputDialog.getText(self,
                                 'Part size',
                                 'What size is the part?')
    return (part_type, purchased_dt, brand, price, weight, sz, model, self.current_bike, "TRUE")

@add_method(StravaApp)
def add_new_part(self):
    parts = self.get_part_inputs(new=True)
    self.add_part(parts)

@add_method(StravaApp)
def add_replacement_part(self):
    pass

@add_method(StravaApp)
def add_part(self, part_values):
    with sqlite3.connect(self.db_path) as conn:
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

@add_method(StravaApp)
def add_maintenance(self):
    # define our input files
    dat = OrderedDict()
    dat['Work'] = 'Enter work summary here'
    dat['Date'] = datetime.date.today().strftime("%Y-%m-%d")

    if get_input(f'Add Maintenance Record for part {self.current_part}', dat):
        dt = dateparser.parse(dat['Date'])
        main_values = (int(self.current_part), dat['Work'], dt)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO maintenance
                            (part, work, date) VALUES (?, ?, ?)""",
                         main_values)

@add_method(StravaApp)
def get_all_bike_parts(self):
    query = f"""SELECT *
                FROM parts 
                WHERE bike = '{self.current_bike}'
                AND inuse = 'TRUE'"""
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        self.current_bike_parts_list = c.fetchall()

@add_method(StravaApp)
def get_all_ride_data(self):
    query = f"SELECT * FROM rides WHERE rider='{self.rider_name}'"
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        self.all_rides = c.fetchall()

@add_method(StravaApp)
def update_part(self):
    query = f"""SELECT distance, elapsed_time, elev
                FROM rides 
                WHERE bike=(SELECT bike_id FROM bikes WHERE name='{self.current_bike}')
                AND date >= (SELECT purchased 
                             FROM parts 
                             WHERE part_id={self.current_part})"""
    with sqlite3.connect(self.db_path) as conn:
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
    self.format_part_info(dist, elev, time)

@add_method(StravaApp)
def add_multiple_rides(self, activity_list):
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
               self.rider_name, ) for a in activity_list]

    with sqlite3.connect(self.db_path) as conn:
        sql = """INSERT INTO rides 
                 (ride_id, bike, distance, name, date, moving_time,
                  elapsed_time, elev, type, avg_speed, max_speed,
                  calories, rider) 
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""" 
        conn.executemany(sql, a_list)

@add_method(StravaApp)
def add_new_bike(self, bike_id, dist, elev, min_date, max_date, special_message=None):
    if self.units == 'imperial':
        dist = str(round(float(dist) / 1.609, 2)) + ' miles'
        elev = str(round(float(elev) * 3.281, 2)) + ' feet'
    else:
        dist = str(round(float(dist), 2)) + ' km'
        elev = str(round(float(elev), 2)) + ' meters'

    name_dialog = f"""Enter a name for the bike with id {bike_id}.\nHere's what we know about this bike: You've ridden it {dist} and {elev}.\nIt was first used on {min_date} and most recently used on {max_date}."""

    if special_message is not None:
        name_dialog = ' '.join([special_message, name_dialog])

    bike_name, _ = QInputDialog.getText(self,
                                        'Bike Name',
                                        name_dialog)

    color_dialog = f"""Enter the color of {bike_name}"""
    purchased_dialog = f"""Enter the purchased date for {bike_name}"""
    price_dialog = f"""Enter the purchase price for{bike_name}"""

    bike_color, _ = QInputDialog.getText(self,
                                         'Bike Name',
                                         color_dialog)
    bike_purchase, _ = QInputDialog.getText(self,
                                            'Bike Name',
                                            purchased_dialog)
    bike_purchase = dateparser.parse(bike_purchase)
    bike_price, _ = QInputDialog.getText(self,
                                         'Bike Name',
                                         price_dialog)
    bike_price = re.sub(r'\$', '', bike_price)

    q = """INSERT INTO bikes
               (bike_id, name, color, purchased, price) 
           VALUES 
               (?, ?, ?, ?, ?)"""
    vals = (bike_id, bike_name, bike_color, bike_purchase, bike_price)
    with sqlite3.connect(self.db_path) as conn:
        conn.execute(q, vals)
        conn.commit()

@add_method(StravaApp)
def add_unknown_bike(self, bike_vals):
    # Run again to make sure we have full list
    self.get_all_bike_ids()
    d = """It looks like you have an unknown bike in your stable.\nThis could be because you haven't set up any bikes in your Strava equipment.\nIt could also be some rides where you did not specify a bike.\nDo you want to treat this as a normal bike or automatically assign its stats to another bike?"""
    action, _ = QInputDialog.getItem(self,
                                     'Unknown bike',
                                     d,
                                     ['Cancel - do nothing',
                                      'Assign to another bike',
                                      'Treat as a regular bike'],
                                     1,
                                     False)
    if action == 'Assign to another bike':
        q = 'SELECT name, bike_id FROM bikes;'
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(q)
            res = c.fetchall()
        if len(res) == 0:
            m = 'Looks like there are no current bikes. Setting Unknown bike as a regular bike.'
            add_new_bike(*bike_vals, special_message=m)
        else:
            b_choice, _ = QInputDialog.getItem(self,
                                               'Which bike?',
                                               'Which bike corresponds to Unknown?',
                                               list(self.all_bike_ids.values()),
                                               0,
                                               False)
            q = f"""SELECT * FROM bikes WHERE name = '{b_choice}';"""
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(q)
                res = c.fetchone()
            q = f"""INSERT INTO bikes
                        (bike_id, name, color, purchased, price) 
                    VALUES 
                        (?, ?, ?, ?, ?)"""
            vals = ('Unknown', b_choice, res[2], res[3], res[4])
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(q, vals)
                conn.commit()
    elif action == 'Treat as a regular bike':
        add_new_bike(*bike_vals)
    else:
        pass

@add_method(StravaApp)
def find_new_bikes(self):
    """Simple function to determine if there are any bikes that haven't been added"""

    # Check what bikes already exist
    self.get_all_bike_ids()

    # And see what bikes appear in rides
    with sqlite3.connect(self.db_path) as conn:
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

    bike_id_keys = list(self.all_bike_ids.keys())
    if len(res) > 0:
        if sum([True if x[0] in bike_id_keys else False for x in res]) == len(bike_id_keys):
            self.msg.setText('No new bikes found.')
        else:
            for item in res:
                if item[0] not in bike_id_keys:
                    if item[0] != 'Unknown':
                        self.add_new_bike(*item)
                    else:
                        self.add_unknown_bike(*item)
    else:
        self.msg.setText('No bikes found in rides! Try updating rides first.')
