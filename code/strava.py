###########################################
# Imports
###########################################
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QInputDialog, QToolTip, QGroupBox, QPushButton, QGridLayout, QMessageBox, QLabel, QButtonGroup, QRadioButton, QComboBox, QCalendarWidget)
from PyQt5.QtGui import QFont
from stravalib.client import Client
from stravalib import unithelper
import configparser, argparse, sqlite3, os, sys, re, requests, keyring, platform, locale
import numpy as np
import pandas as pd
from functools import partial

###########################################
# Application Class
###########################################
class StravaApp(QWidget):
    def __init__(self, schema, client):
        super().__init__()
        self.schema = schema
        self.client = client
        self.get_path()
        self.test_os()
        self.try_load_db()
        self.load_db()
        self.try_get_password()
        self.load_basic_values()
        self.initUI()

    def load_basic_values(self):
        self.current_part = None
        self.rider = self.get_rider_info()
        self.get_all_ride_ids()
        # self.current_bike = None

    def get_all_ride_ids(self):
        query = "SELECT id FROM rides WHERE rider='%s'" % self.rider_name
        all_ride_ids = self.get_from_db(query)
        self.id_list = list(all_ride_ids['id'])

    def get_rider_info(self):
        query = 'select * from riders'
        res = self.get_from_db(query)
        self.rider_name = res['name'][0]
        self.max_speed = res['max_speed'][0]
        self.avg_speed = res['avg_speed'][0]
        self.tot_dist = res['total_dist'][0]
        self.tot_climb = res['total_climb'][0]
        self.units = res['units'][0]
        return res

    def test_os(self):
        system = platform.system()
        if system == 'Windows':
            self.init_dir = 'C:\\Documents\\'
        else:
            self.init_dir = os.path.expanduser('~/Documents/')
            
    def get_path(self):
        """Defines a base directory in which application files are held"""
        try:
            self.bdr = sys._MEIPASS
        except:
            self.bdr = os.path.dirname(os.path.abspath(__file__))

    def try_load_db(self):
        """Define the database file location or initialize new if none exists"""
        if os.path.exists(os.path.expanduser('~/.stravaDB_location')):
            with open(os.path.expanduser('~/.stravaDB_location'), 'r') as f:
                self.db_path = f.read().strip()
        else:
            self.init_new_db()

    def init_new_db(self):
        """Function to initialize a new DB using a pop-up dialogue"""
        db_path, ok = QFileDialog.getOpenFileName(self,
                                                      caption='Selection location to save database file',
                                                      directory=self.init_dir,
                                                      filter='database files(*.db)')
        if ok:
            self.db_path = db_path
            with open(os.path.expanduser('~/.stravaDB_location'), 'w') as f:
                f.write(db_path)
            self.create_db()
        else:
            self.init_new_db()
        rider_name, _ = QFileDialog.getText(self,
                                                    'Rider Name',
                                                    'Enter rider name')
        self.initialize_rider(rider_name)

    def initialize_rider(self, rider_name):
        rider_values = (rider_name, 'imperial')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT into riders (name, units) 
                            values (?, ?)""",
                         rider_values)

    def edit_entry(self, sql, values):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, values)

    def create_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.schema)


    def try_get_password(self):
        """Attempts to get Strava application information, else prompts for input"""
        code = keyring.get_password('stravaDB', 'code')
        if code is not None:
            self.code = code
        else:
            text, ok = QInputDialog.getText(self,
                                            'Application Code',
                                            'Enter application code:')
            if ok:
                self.code = str(text)
                keyring.set_password('stravaDB', 'code', str(text))
        secret = keyring.get_password('stravaDB', 'client_secret')
        if secret is not None:
            self.client_secret = secret
        else:
            text, ok = QInputDialog.getText(self,
                                            'Client Secret',
                                            'Enter client secret:')
            if ok:
                self.client_secret = str(text)
                keyring.set_password('stravaDB', 'client_secret', str(text))
        cid = keyring.get_password('stravaDB', 'client_id')
        if cid is not None:
            self.client_id = cid
        else:
            text, ok = QInputDialog.getText(self,
                                            'Client ID',
                                            'Enter client id:')
            if ok:
                self.client_id = str(text)
                keyring.set_password('stravaDB', 'client_id', str(text))

    def load_db(self):
        self.get_all_bike_ids()

    def get_from_db(self, query):
        with sqlite3.connect(self.db_path) as conn:
            res = pd.read_sql_query(query, conn)
        return res

    def get_all_bike_ids(self):
        query = "SELECT id, name from bikes"
        self.all_bike_ids = self.get_from_db(query)

    def replace_part(self, old_part=None):
        # need to get some kind of popup here to input part values!
        self.add_part(part_values)
        if old_part is not None:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('UPDATE parts SET inuse = False WHERE id=?',
                             (old_part, ))

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

    def add_maintenance(self):
        # need to get some kind of popup here to input part values!
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT into maintenance 
                            (part, work, date) values (?, ?, ?)""",
                         main_values)

    def get_all_bike_parts(self):
        sql = """SELECT * 
                 FROM parts 
                 WHERE bike = '%s'""" %self.current_bike
        self.current_bike_parts_list = self.get_from_db(sql)
        

    def bike_choice(self, b):
        self.current_bike = b
        self.get_all_bike_parts()
        self.change_parts_list()
        # self.mb(b)

    def part_choice(self, p):
        if p >= 1:
            self.current_part = self.current_bike_parts_list.id[p - 1]
            self.format_part_info()
        else:
            self.part_stats.setText('')

    def select_date(self, d):
        self.current_date = d

    def get_all_ride_data(self):
        query = "SELECT * from rides WHERE rider='%s'" % self.rider_name
        with sqlite3.connect(self.db_path) as conn:
            self.all_rides = pd.read_sql_query(query, conn)

    def update_rider(self):
        # want to calculate max and avg speeds
        self.get_all_ride_data()
        try:
            ms = np.round(self.all_rides['max_speed'].max(), 2)
        except:
            ms = None
        try:
            av = np.round(self.all_rides['avg_speed'].mean(), 2)
        except:
            av = None
        try:
            tot = np.round(self.all_rides['distance'].sum(), 2)
        except:
            tot = None
        try:
            tot_c = np.round(self.all_rides['elev'].sum(), 2)
        except:
            tot_c = None
        self.max_speed = ms
        self.avg_speed = av
        self.tot_dist = tot
        self.tot_elev = tot_c
        sql = """UPDATE riders 
             SET max_speed = ?, avg_speed = ?, total_dist = ?, total_climb = ?
             WHERE name = ?"""
        self.edit_entry(sql, (ms, av, tot, tot_c, self.rider_name))

    def change_parts_list(self):
        bpl = self.current_bike_parts_list[['id', 'type']]
        p_list = bpl['type']
        self.parts_list_menu.addItems(list(p_list))

    def format_part_info(self):
        sql = """SELECT * 
                 FROM parts 
                 WHERE id = %i""" %self.current_part
        res = self.get_from_db(sql)
        t = res.T.to_string(header=False)
        t = re.sub(r'^(.*?) ', r'<b>\1:</b> ', t, flags=re.M)
        t = re.sub(r'\n', '<br>', t)
        self.part_stats.setText(t)

    def format_rider_info(self, update=False):
        if update:
            self.update_rider()
        rider = self.get_rider_info()
        u = rider.units[0]
        t_dist = int(np.round(rider.total_dist[0]))
        t_dist = f'{t_dist:n}'
        t_climb = int(np.round(rider.total_climb[0]))
        t_climb = f'{t_climb:n}'
        rider = rider.reindex(columns=['name',
                                       'max_speed',
                                       'avg_speed',
                                       'total_dist',
                                       'total_climb',
                                       'units'])
        rider.rename(columns={'name': '<b>Name:</b> ',
                              'max_speed': '<b>Max Speed:</b> ',
                              'avg_speed': '<b>Average Speed:</b> ',
                              'total_dist': '<b>Total Distance:</b> ',
                              'total_climb': '<b>Total Elevation Gain:</b> ', 
                              'units': '<b>Units:</b> '},
                     inplace=True)
        t = rider.T.to_string(header=False)
        t = re.sub(r'\n', '<br>', t)
        if u == 'imperial':
            t = re.sub(r'(Max Speed.*?)<br>', r'\1 mph<br>', t)
            t = re.sub(r'(Average Speed.*?)<br>', r'\1 mph<br>', t)
            t = re.sub(r'(Total Distance.*?)<br>',
                       'Total Distance:</b> %s miles<br>' %t_dist, t)
            t = re.sub(r'(Total Elevation Gain.*?)<br>',
                       'Total Elevation Gain:</b> %s feet<br>' %t_climb, t)
        else:
            t = re.sub(r'(^Max Speed.*?)', r'\1 kph', t)
            t = re.sub(r'(^Average Speed.*?)', r'\1 kph', t)
            t = re.sub(r'(Total Distance.*?)<br>',
                       'Total Distance:</b> %s kilometers<br>' %t_dist, t)
            t = re.sub(r'(Total Elevation Gain.*?)<br>',
                       'Total Elevation Gain:</b> %s meters<br>' %t_climb, t)
        if update:
            self.rider_info.setText(t)
        else:
            return t

    def test_conn(self):
        try:
            _ = requests.get('http://www.google.com', timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def gen_secrets(self):
        tr = self.client.exchange_code_for_token(client_id=self.client_id,
                                                 client_secret=self.client_secret,
                                                 code=self.code)
        self.client.access_token = tr['access_token']
        self.client.refresh_token = tr['refresh_token']
        self.client.expires_at = tr['expires_at']

    def fetch_new_activities(self):
        self.get_all_ride_ids()
        if self.test_conn():
            self.gen_secrets()
            activity_list = self.client.get_activities()
            if self.id_list is not None:
                self.new_id_list = [x.id for x in activity_list
                                    if (x.id not in self.id_list and x.type == "Ride")]
            else:
                self.new_id_list = [x.id for x in activity_list]
            if len(self.new_id_list) > 0:
                self.new_activities = [self.client.get_activity(id) for id
                                       in self.new_id_list]
                self.mb('Fetched %i new activities' %len(self.new_id_list))
            else:
                self.new_activities = None
                self.mb('No new activities.')
        else:
            self.mb("No internet connection. Unable to update rides.")
            self.new_activities = None

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
            sql = """INSERT into rides 
                     (id, bike, distance, name, date, moving_time,
                      elapsed_time, elev, type, avg_speed, max_speed,
                      calories, rider) 
                     values (?,?,?,?,?,?,?,?,?,?,?,?,?)""" 
            conn.executemany(sql, a_list)


    def new_activities(self):
        self.fetch_new_activities()
        if self.new_id_list is not None:
            self.add_multiple_rides(self.new_activities)

    def mb(self, s):
        self.message.setText(s)
            
    def initUI(self):
        """Main GUI definition"""
        QToolTip.setFont(QFont('SansSerif', 10))

        # Create all of the objects
        ### Left Column
        #### Upper left column box
        self.upper_left_col_box = QGroupBox("Rider Info")
        self.rider_info = QLabel(self)
        self.rider_info.setTextFormat(Qt.RichText)
        self.rider_info.setWordWrap(True)
        self.rider_info.setAlignment(Qt.AlignTop)
        self.rider_info.setText(self.format_rider_info())

        up_rider = QPushButton('Update Rider Stats', self)
        up_rider.setToolTip('Update max speed, average speed, and total distance')
        up_rider.clicked.connect(lambda: self.format_rider_info(update=True))

        up_rides = QPushButton('Fetch New Rides', self)
        up_rides.setToolTip('Fetch new rides from Strava and update rider stats')
        up_rides.clicked.connect(self.new_activities)

        rider_layout = QGridLayout()
        rider_layout.addWidget(self.rider_info, 0, 0)
        rider_layout.addWidget(up_rider, 1, 0)
        rider_layout.addWidget(up_rides, 1, 1)
        self.upper_left_col_box.setLayout(rider_layout)

        #### Middle row left column box
        self.mid_left_col_box = QGroupBox('Bike and Part Selection')
        bike_list = QComboBox()
        bike_list.addItems(list(self.all_bike_ids.name))
        bike_list.activated[str].connect(self.bike_choice)

        self.parts_list_menu = QComboBox(self)
        self.parts_list_menu.addItem(None)
        self.parts_list_menu.currentIndexChanged.connect(self.part_choice)

        bike_dropdown_layout = QGridLayout()
        bike_dropdown_layout.addWidget(bike_list, 0, 0)
        bike_dropdown_layout.addWidget(self.parts_list_menu, 1, 0)
        self.mid_left_col_box.setLayout(bike_dropdown_layout)

        #### Lower left column box
        self.lower_left_col_box = QGroupBox('')
        cal = QCalendarWidget()
        cal.setGridVisible(True)
        cal.clicked[QDate].connect(self.select_date)
        self.date = cal.selectedDate().toString()

        cal_layout = QGridLayout()
        cal_layout.addWidget(cal, 0, 0)
        self.lower_left_col_box.setLayout(cal_layout)

        ### Right Column
        #### Upper right column box
        self.upper_right_col_box = QGroupBox('Part Stats')
        self.part_stats = QLabel(self)
        self.part_stats.setTextFormat(Qt.RichText)
        self.part_stats.setWordWrap(True)
        self.part_stats.setAlignment(Qt.AlignTop)
        self.part_stats.setText('')

        part_stats_layout = QGridLayout()
        part_stats_layout.addWidget(self.part_stats, 0, 0)
        self.upper_right_col_box.setLayout(part_stats_layout)

        #### Lower right column box
        self.lower_right_col_box = QGroupBox('Part Actions')

        ##### buttons!
        replace_part_button = QPushButton('Replace part', self)
        replace_part_button.setToolTip('Replace currently selected part')
        replace_part_button.clicked.connect(partial(self.replace_part,
                                                    old_part=self.current_part))
        new_part_button = QPushButton('Add new part', self)
        new_part_button.setToolTip("""Add a new part to the bike.
                                      NOTE: This is different from replacing an
                                      existing part""")
        new_part_button.clicked.connect(self.replace_part)
        maintain_button = QPushButton('Maintain part', self)
        maintain_button.setToolTip("Perform maintenance on selected part")
        maintain_button.clicked.connect(self.add_maintenance)

        parts_buttons_layout = QGridLayout()
        parts_buttons_layout.addWidget(maintain_button, 0, 0)
        parts_buttons_layout.addWidget(replace_part_button, 1, 0)
        parts_buttons_layout.addWidget(new_part_button, 0, 1)
        self.lower_right_col_box.setLayout(parts_buttons_layout)

        ##### Message box
        self.message_box = QGroupBox()

        # messages
        self.message = QLabel(self)
        self.message.setText('')
        mes_layout = QGridLayout()
        mes_layout.addWidget(self.message, 0, 0)
        self.message_box.setLayout(mes_layout)

        # Generate the main layout
        main_layout = QGridLayout()
        main_layout.addWidget(self.upper_left_col_box, 0, 0, 4, 1)
        main_layout.addWidget(self.mid_left_col_box, 4, 0, 1, 1)
        main_layout.addWidget(self.lower_left_col_box, 5, 0, 4, 1)
        main_layout.addWidget(self.upper_right_col_box, 0, 1, 5, 1)
        main_layout.addWidget(self.lower_right_col_box, 5, 1, 4, 1)
        main_layout.addWidget(self.message_box, 9, 0, 1, 2)
        main_layout.setColumnStretch(0, 1) # args are col number and relative weight
        main_layout.setColumnStretch(1, 1)
        self.setLayout(main_layout)

        # Set window traits
        self.setGeometry(300, 300, 1050, 700)
        self.setWindowTitle('Strava Equipment Manager')
        self.show()


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    strava_db_schema = """
    -- Riders are top level
    create table riders (
        name       text primary key,
        max_speed   real,
        avg_speed   real,
        total_dist  real,
        total_climb real, 
        units       text
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

    cl = Client()
    app = QApplication(sys.argv)
    strava_app = StravaApp(strava_db_schema, cl)
    sys.exit(app.exec_())
