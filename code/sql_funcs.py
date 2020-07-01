###########################################
# Imports
###########################################
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QInputDialog, QToolTip, QGroupBox, QPushButton, QGridLayout, QMessageBox, QLabel, QButtonGroup, QRadioButton, QComboBox, QCalendarWidget, QLineEdit)
from PyQt5.QtGui import QFont
from stravalib.client import Client
from stravalib import unithelper
import configparser, argparse, sqlite3, os, sys, re, requests, keyring, platform, locale, datetime
from functools import partial
from input_form_dialog import FormOptions, get_input
from base_class import add_method, StravaApp

@add_method(StravaApp)
def get_all_bike_ids(self):
    query = "SELECT bike_id, name FROM bikes"
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        self.all_bike_ids = {x[0]: x[1] for x in c.fetchall()}

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
        try:
            c.execute('SELECT MAX(max_speed) FROM rides')
            self.max_speed = round(c.fetchone()[0], 2)
        except:
            self.max_speed = 0
        try:
            c.execute('SELECT AVG(avg_speed) FROM rides') # is this correct?
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
    # need to get some kind of popup here to input part values!
    self.add_part(part_values)
    if old_part is not None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE parts SET inuse = 'True' WHERE part_id=?",
                         (old_part, ))
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
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, True)""", part_values)

@add_method(StravaApp)
def add_maintenance(self):
    # Define today
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    # define our input files
    dat = dict()
    dat['Work'] = 'Work summary'
    dat['Date'] = current_date

    if get_input(f'Add Maintenance Record for part {self.current_part}', dat):
        main_values = (int(self.current_part), dat['Work'], dat['Date'])
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO maintenance 
                            (part, work, date) VALUES (?, ?, ?)""",
                         main_values)

@add_method(StravaApp)
def get_all_bike_parts(self):
    query = f"""SELECT * 
                FROM parts 
                WHERE bike = '{self.current_bike}'
                AND inuse = 'True'"""
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
    def unit_try(num, t, u):
        if u == 'imperial':
            if t == 'long_dist':
                return float(unithelper.miles(num))
            elif t == 'short_dist':
                return float(unithelper.feet(num))
            elif t == 'speed':
                return float(unithelper.mph(num))
        else:
            if t == 'long_dist':
                return float(unithelper.kilometers(num))
            elif t == 'short_dist':
                return float(unithelper.meters(num))
            elif t == 'speed':
                return float(unithelper.kph(num))
    a_list = [(a.id,
               gear_try(a),
               unit_try(a.distance, 'long_dist', self.units), 
               a.name,
               a.start_date.strftime("%Y-%M-%d"), 
               a.moving_time.seconds / 3600,
               a.elapsed_time.seconds / 3600,
               unit_try(a.total_elevation_gain, 'short_dist', self.units),
               a.type,
               unit_try(a.average_speed, 'speed', self.units), 
               unit_try(a.max_speed, 'speed', self.units),
               float(a.calories),
               self.rider_name, ) for a in activity_list]

    with sqlite3.connect(self.db_path) as conn:
        sql = """INSERT INTO rides 
                 (ride_id, bike, distance, name, date, moving_time,
                  elapsed_time, elev, type, avg_speed, max_speed,
                  calories, rider) 
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""" 
        conn.executemany(sql, a_list)

