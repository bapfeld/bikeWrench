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
from base_class import StravaApp
import startup_funcs
import sql_funcs
import strava_interaction
import gui


def initialize_params():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--schema_path',
        help="Path to the create_db.sql script",
        required=True,
    )
    return parser.parse_args()

def main():
    locale.setlocale(locale.LC_ALL, '')
    args = initialize_params()
    schema_path = os.path.expanduser(args.schema_path)
    with open(schema_path, 'r') as f:
        strava_db_schema = f.read()
    cl = Client()
    app = QApplication(sys.argv)
    strava_app = StravaApp(strava_db_schema, cl)
    strava_app.get_path()
    strava_app.test_os()
    strava_app.try_load_db()
    strava_app.load_db()
    strava_app.try_get_password()
    strava_app.load_basic_values()
    strava_app.initUI()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
