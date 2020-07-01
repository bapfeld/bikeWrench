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
def mb(self, s):
    self.message.setText(s)

@add_method(StravaApp)
def bike_choice(self, b):
    self.current_bike = b
    self.get_all_bike_parts()
    self.change_parts_list()
    # self.mb(b)

@add_method(StravaApp)
def part_choice(self, p):
    if p >= 1:
        self.current_part = self.current_bike_parts_list[p][0]
        self.format_part_info()
    else:
        self.part_stats.setText('')

@add_method(StravaApp)
def select_date(self, d):
    self.current_date = d

@add_method(StravaApp)
def change_parts_list(self):
    p_list = [x[1] for x in self.current_bike_parts_list]
    self.parts_list_menu.clear()
    self.parts_list_menu.addItems(list(p_list))

@add_method(StravaApp)
def format_part_info(self, dist=None, elev=None, time=None):
    # Part Stats
    query = """SELECT * 
               FROM parts 
               WHERE part_id = {self.current_part}"""
    with sqlite3.connect(self.db_path) as conn:
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
    with sqlite3.connect(self.db_path) as conn:
        c = conn.cursor()
        c.execute(query)
        main_res = c.fetchall()
    t = ''
    if len(main_res) > 0:
        for rec in main_res:
            t += f"""<b>Date:</b> {rec[3]}<br>
                     <b>Work done:</b> {rec[2]}<br>"""
    self.part_main.setText(t)

@add_method(StravaApp)
def format_rider_info(self, update=False):
    self.get_rider_info()
    self.convert_rider_info()
    t = f"""<b>Name:</b> {self.rider_name}<br>
            <b>Max Speed:</b> {self.max_speed}<br>
            <b>Average Speed:</b> {self.avg_speed}<br>
            <b>Total Distance:</b> {self.tot_dist}<br>
            <b>Total Elevation Gain:</b> {self.tot_climb}<br>
            <b>Units:</b> {self.units}"""
    if self.units == 'imperial':
        t = re.sub(r'(Max Speed.*?)<br>', r'\1 mph<br>', t)
        t = re.sub(r'(Average Speed.*?)<br>', r'\1 mph<br>', t)
        t = re.sub(r'(Total Distance.*?)<br>', r'\1 miles<br>', t)
        t = re.sub(r'(Total Elevation Gain.*?)<br>', r'\1 feet<br>', t)
    else:
        t = re.sub(r'(^Max Speed.*?)<br>', r'\1 kph<br>', t)
        t = re.sub(r'(^Average Speed.*?)<br>', r'\1 kph<br>', t)
        t = re.sub(r'(Total Distance.*?)<br>', r'\1 kilometers<br>', t)
        t = re.sub(r'(Total Elevation Gain.*?)<br>', r'\1 meters<br>', t)
    if update:
        self.rider_info.setText(t)
    else:
        return t


@add_method(StravaApp)
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
    up_rides.clicked.connect(lambda: self.get_new_activities())

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
