###########################################
# Imports
###########################################
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QInputDialog, QToolTip, QGroupBox, QPushButton, QGridLayout, QMessageBox, QLabel, QButtonGroup, QRadioButton, QComboBox, QCalendarWidget, QLineEdit)
from PyQt5.QtGui import QFont
from stravalib.client import Client
from stravalib import unithelper
import configparser, argparse
import sqlite3
import os, sys, platform
import locale, datetime, time
import re
import requests
import keyring
from functools import partial
from input_form_dialog import FormOptions, get_input
from base_class import add_method, StravaApp

@add_method(StravaApp)
def test_conn(self):
    try:
        _ = requests.get('http://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False

@add_method(StravaApp)
def reset_secrets(self, tkn):
    self.client.access_token = tkn['access_token']
    self.client.refresh_token = tkn['refresh_token']
    self.client.expires_at = tkn['expires_at']
    with sqlite3.connect(self.db_path) as conn:
        q = f"""UPDATE
                    riders
                SET
                    r_tkn='{self.client.refresh_token}',
                    tkn_exp={self.client.expires_at}
                WHERE
                    name='{self.rider_name}'"""
        c = conn.cursor()
        c.execute(q)

@add_method(StravaApp)
def gen_secrets(self):
    if self.client.refresh_token is None:
        tkn = self.client.exchange_code_for_token(client_id=self.client_id,
                                                  client_secret=self.client_secret,
                                                  code=self.code)
        self.reset_secrets(tkn)
    elif datetime.datetime.now() > self.client.expires_at:
        tkn = self.client.refresh_access_token(client_id=self.client_id,
                                               client_secret=self.client_secret,
                                               refresh_token=self.client.refresh_token)
        self.reset_secrets(tkn)
    else:
        pass

@add_method(StravaApp)
def fetch_new_activities(self):
    self.get_all_ride_ids()
    if self.test_conn():
        self.gen_secrets()
        activity_list = self.client.get_activities()
        if activity_list is not None:
            if self.id_list is not None:
                self.new_id_list = [x.id for x in activity_list
                                    if (x.id not in self.id_list and x.type == "Ride")]
            else:
                self.new_id_list = [x.id for x in activity_list]
            if len(self.new_id_list) > 0:
                self.new_activities = [self.client.get_activity(id) for id
                                       in self.new_id_list]
                self.mb(f'Fetched {len(self.new_id_list)} new activities')
            else:
                self.new_activities = None
                self.mb('No new activities.')
        else:
            self.new_activities = None
            self.mb('No new activities.')
    else:
        self.mb("No internet connection. Unable to update rides.")
        self.new_activities = None

@add_method(StravaApp)
def get_new_activities(self):
    self.fetch_new_activities()
    if self.new_activities is not None:
        self.add_multiple_rides(self.new_activities)
    self.find_new_bikes()
