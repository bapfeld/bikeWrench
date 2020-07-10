###########################################
# Imports
###########################################
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QInputDialog, QToolTip, QGroupBox, QPushButton, QGridLayout, QMessageBox, QLabel, QButtonGroup, QRadioButton, QComboBox, QCalendarWidget, QLineEdit)
from PyQt5.QtGui import QFont
from stravalib.client import Client
from stravalib import unithelper
import configparser, argparse, sqlite3, os, sys, re, requests, keyring, platform, locale, datetime
from functools import partial, wraps
from input_form_dialog import FormOptions, get_input

###########################################
# Decorator func to allow extending class
###########################################       
def add_method(cls):
    def decorator(func):
        @wraps(func) 
        def wrapper(*args, **kwargs): 
            return func(*args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        return func
    return decorator

class StravaApp(QWidget):
    def __init__(self, schema, client, parts_dict):
        super().__init__()
        self.schema = schema
        self.client = client
        self.parts_dict = parts_dict
