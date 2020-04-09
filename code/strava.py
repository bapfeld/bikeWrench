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
        self.get_rider_info()
        self.get_all_ride_ids()
        # self.current_bike = None

    def get_all_ride_ids(self):
        query = f"SELECT ride_id FROM rides WHERE rider='{self.rider_name}'"
        with sqlite.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query)
            self.id_list = [x[0] for x in c.fetchall()]

    def get_rider_info(self):
        with sqlite.connect(self.db_path) as conn:
            c = conn.cursor()
            try:
                c.execute('SELECT MAX(max_speed) FROM rides')
                self.max_speed = round(c.fetchone()[0], 2)
            except:
                self.max_speed = None
            try:
                c.execute('SELECT MEAN(avg_speed) FROM rides') # is this correct?
                self.avg_speed = round(c.fetchone()[0], 2)
            except:
                self.avg_speed = None
            try:
                c.execute('SELECT SUM(distance) FROM rides')
                self.tot_dist = round(c.fetchone()[0], 2)
            except:
                self.tot_dist = None
            try:
                c.execute('SELECT SUM(elev) FROM rides')
                self.tot_climb = round(c.fetchone()[0], 2)
            except:
                self.tot_climb = None
            c.execute('SELECT * FROM riders')
            res = c.fetchone()
            self.rider_name = res[0][0]
            self.units = res[0][1]

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

    def initialize_rider(self, rider_name):
        rider_values = (rider_name, 'imperial')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT into riders (name, units) 
                            VALUES (?, ?)""",
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

    def load_db(self):
        self.get_all_bike_ids()

    def get_all_bike_ids(self):
        query = "SELECT bike_id, name FROM bikes"
        with sqlite.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query)
            self.all_bike_ids = {x[0]: x[1] for x in c.fetchall()}

    def replace_part(self, old_part=None):
        # need to get some kind of popup here to input part values!
        self.add_part(part_values)
        if old_part is not None:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE parts SET inuse = 'True' WHERE part_id=?",
                             (old_part, ))

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

    def get_all_bike_parts(self):
        query = f"""SELECT * 
                    FROM parts 
                    WHERE bike = '{self.current_bike}'
                    AND inuse = 'True'"""
        with sqlite.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query)
            self.current_bike_parts_list = c.fetchall()
        

    def bike_choice(self, b):
        self.current_bike = b
        self.get_all_bike_parts()
        self.change_parts_list()
        # self.mb(b)

    def part_choice(self, p):
        if p >= 1:
            self.current_part = self.current_bike_parts_list[p][0]
            self.format_part_info()
        else:
            self.part_stats.setText('')

    def select_date(self, d):
        self.current_date = d

    def get_all_ride_data(self):
        query = f"SELECT * FROM rides WHERE rider='{self.rider_name}'"
        with sqlite.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query)
            self.all_rides = c.fetchall()

    def update_part(self):
        query = f"""SELECT distance, elapsed_time, elev 
                    FROM rides 
                    WHERE bike=(SELECT bike_id FROM bikes WHERE name='{self.current_bike}')
                    AND date >= (SELECT purchased 
                                 FROM parts 
                                 WHERE part_id={self.current_part})"""
        with sqlite.connect(self.db_path) as conn:
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

    def change_parts_list(self):
        p_list = [x[1] for x in self.current_bike_parts_list]
        self.parts_list_menu.clear()
        self.parts_list_menu.addItems(list(p_list))

    def format_part_info(self, dist=None, elev=None, time=None):
        # Part Stats
        query = """SELECT * 
                   FROM parts 
                   WHERE part_id = {self.current_part}"""
        with sqlite.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query)
            res = c.fetchone()
        t = f"""<b>Part ID:</b> {res[0]}<br>
                <b>Type:</b> {res[1]}<br>
                <b>Purchased:</b> {res[2]}<br>
                <b>Brand:</b> {res[3]}<br>
                <b>Weight:</b> {res[4]}<br>
                <b>Size:</b> {res[5]}<br>
                <b>Model:</b> {res[6]}<br>
                <b>Bike:</b> {res[7]}<br>"""
        if dist is not None:
            t += f'<br><br><b>Total Distance:</b> {dist}'
        if elev is not None:
            t += f'<br><b>Total Elevation:</b> {elev}'
        if time is not None:
            t += f'<br><b>Total Time:</b> {time}'
        self.part_stats.setText(t)
        

        # Part Maintenance
        query = f"""SELECT work, date
                    FROM maintenance
                    WHERE part_id={self.current_part}"""
        with sqlite.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query)
            main_res = c.fetchall()
        t = ''
        if len(main_res) > 0:
            for rec in main_res:
                t += f"""<b>Date:</b> {rec[3]}<br>
                         <b>Work done:</b> {rec[2]}<br>"""
        self.part_main.setText(t)

    def format_rider_info(self):
        self.get_rider_info()
        t = f"""<b>Name:</b> {self.rider_name}<br>
                <b>Max Speed:</b> {self.max_speed}<br>
                <b>Average Speed:</b> {self.avg_speed}<br>
                <b>Total Distance:</b> {int(self.tot_dist)}<br>
                <b>Total Elevation Gain:</b> {int(self.tot_climb)}<br>
                <b>Units:</b> {self.units}"""
        if self.units == 'imperial':
            t = re.sub(r'(Max Speed.*?)<br>', r'\1 mph<br>', t)
            t = re.sub(r'(Average Speed.*?)<br>', r'\1 mph<br>', t)
            t = re.sub(r'(Total Distance:</b> (.*?))<br>',
                       'Total Distance:</b> \2 miles<br>', t)
            t = re.sub(r'(Total Elevation Gain:<b> (.*?))<br>',
                       'Total Elevation Gain:</b> \2 feet<br>', t)
        else:
            t = re.sub(r'(^Max Speed.*?)', r'\1 kph', t)
            t = re.sub(r'(^Average Speed.*?)', r'\1 kph', t)
            t = re.sub(r'(Total Distance:</b> (.*?))<br>',
                       'Total Distance:</b> \2 kilometers<br>', t)
            t = re.sub(r'(Total Elevation Gain:</b> (.*?))<br>',
                       'Total Elevation Gain:</b> \2 meters<br>', t)
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

    def new_activities(self):
        self.fetch_new_activities()
        if self.new_activities is not None:
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
        up_rider.clicked.connect(lambda: self.format_rider_info())

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
        bike_list.addItems(self.all_bike_ids.values())
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

        #### Middle right column box
        self.middle_right_col_box = QGroupBox('Part Maintenance')
        self.part_main = QLabel(self)
        self.part_main.setTextFormat(Qt.RichText)
        self.part_main.setWordWrap(True)
        self.part_main.setAlignment(Qt.AlignTop)
        self.part_main.setText('')

        part_main_layout = QGridLayout()
        part_main_layout.addWidget(self.part_main, 0, 0)
        self.middle_right_col_box.setLayout(part_main_layout)

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
        update_part_button = QPushButton('Update Part Stats', self)
        update_part_button.setToolTip('Update currently selected part')
        update_part_button.clicked.connect(self.update_part)
        

        parts_buttons_layout = QGridLayout()
        parts_buttons_layout.addWidget(maintain_button, 0, 0)
        parts_buttons_layout.addWidget(replace_part_button, 1, 0)
        parts_buttons_layout.addWidget(new_part_button, 0, 1)
        parts_buttons_layout.addWidget(update_part_button, 1, 1)
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
        main_layout.addWidget(self.lower_left_col_box, 7, 0, 4, 1)
        main_layout.addWidget(self.upper_right_col_box, 0, 1, 4, 1)
        main_layout.addWidget(self.middle_right_col_box, 4, 1, 3, 1)
        main_layout.addWidget(self.lower_right_col_box, 7, 1, 4, 1)
        main_layout.addWidget(self.message_box, 11, 0, 1, 2)
        main_layout.setColumnStretch(0, 1) # args are col number and relative weight
        main_layout.setColumnStretch(1, 1)
        self.setLayout(main_layout)

        # Set window traits
        self.setGeometry(300, 300, 1050, 700)
        self.setWindowTitle('Strava Equipment Manager')
        self.show()


def initialize_params():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--schema_path',
        help="Path to the create_db.sql script",
        required=True,
    )
    return parser.parse_args()


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    args = initialize_params()
    schema_path = os.path.expanduser(args.schema_path)
    with open(schema_path, 'r') as f:
        strava_db_schema = f.read()
    cl = Client()
    app = QApplication(sys.argv)
    strava_app = StravaApp(strava_db_schema, cl)
    sys.exit(app.exec_())
