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
def get_path(self):
    """Defines a base directory in which application files are held"""
    try:
        self.bdr = sys._MEIPASS
    except:
        self.bdr = os.path.dirname(os.path.abspath(__file__))

@add_method(StravaApp)
def test_os(self):
    system = platform.system()
    if system == 'Windows':
        self.init_dir = 'C:\\Documents\\'
    else:
        self.init_dir = os.path.expanduser('~/Documents/')

@add_method(StravaApp)
def try_load_db(self):
    """Define the database file location or initialize new if none exists"""
    if os.path.exists(os.path.expanduser('~/.stravaDB_location')):
        with open(os.path.expanduser('~/.stravaDB_location'), 'r') as f:
            self.db_path = f.read().strip()
    else:
        self.init_new_db()

@add_method(StravaApp)
def init_new_db(self):
    """Function to initialize a new DB using a pop-up dialogue"""
    db_path, ok = QFileDialog.getOpenFileName(self,
                                              caption='Select location to save database file',
                                              directory=self.init_dir,
                                              filter='database files(*.db)')
    if ok:
        self.db_path = db_path
        with open(os.path.expanduser('~/.stravaDB_location'), 'w') as f:
            f.write(db_path)
        if not os.path.exists(self.db_path):
            self.create_db()
            rider_name, _ = QFileDialog.getText(self,
                                                'Rider Name',
                                                'Enter rider name')
            self.initialize_rider(rider_name)
    else:
        self.init_new_db()

@add_method(StravaApp)
def initialize_rider(self, rider_name):
    rider_values = (rider_name, 'imperial')
    with sqlite3.connect(self.db_path) as conn:
        conn.execute("""INSERT into riders (name, units) 
                        VALUES (?, ?)""",
                     rider_values)

@add_method(StravaApp)
def create_db(self):
    with sqlite3.connect(self.db_path) as conn:
        conn.executescript(self.schema)@add_method(StravaApp)

@add_method(StravaApp)
def load_db(self):
    self.get_all_bike_ids()

@add_method(StravaApp)
def try_get_password(self):
    """Attempts to get Strava application information, else prompts for input"""
    code = keyring.get_password('stravaDB', 'code')
    secret = keyring.get_password('stravaDB', 'client_secret')
    cid = keyring.get_password('stravaDB', 'client_id')
    if code is not None:
        self.code = code
    else:
        text, ok = QInputDialog.getText(self,
                                        'Application Code',
                                        'Enter application code:')
        if ok:
            self.code = str(text)
            keyring.set_password('stravaDB', 'code', str(text))
    if secret is not None:
        self.client_secret = secret
    else:
        text, ok = QInputDialog.getText(self,
                                        'Client Secret',
                                        'Enter client secret:')
        if ok:
            self.client_secret = str(text)
            keyring.set_password('stravaDB', 'client_secret', str(text))
    if cid is not None:
        self.client_id = cid
    else:
        text, ok = QInputDialog.getText(self,
                                        'Client ID',
                                        'Enter client id:')
        if ok:
            self.client_id = str(text)
            keyring.set_password('stravaDB', 'client_id', str(text))

@add_method(StravaApp)
def load_basic_values(self):
    self.current_part = None
    self.get_rider_info()
    self.get_all_ride_ids()
    # self.current_bike = None
