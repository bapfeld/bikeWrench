import os
import sqlite3
import datetime
import dateparser
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, url_for
from stravalib import unithelper
# from wtforms import (Form, TextField, TextAreaField,
#                      validators, StringField, SubmitField)

###########################################################################
# Initial Setup                                                           #
###########################################################################
app = Flask(__name__)
load_dotenv(find_dotenv())
db_path = os.environ.get('STRAVA_DB_PATH')
bdr = os.environ.get('BDR')
schema_path = os.environ.get('SCHEMA_PATH')


###########################################################################
# Database functions                                                      #
###########################################################################
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
    return (max_speed, avg_speed, tot_dist, tot_climb)


def update_rider(current_nm, nm, units, db_path):
    q = f"""UPDATE riders 
            SET name = '{nm}', 
                units = '{units}' 
            WHERE name = '{current_nm}'"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(q)


###########################################################################
# App helper funcs                                                        #
###########################################################################
def units_text(unit_type):
    if unit_type == 'imperial':
        speed_unit = 'MPH'
        dist_unit = 'miles'
        elev_unit = 'feet'
    else:
        speed_unit = 'KPH'
        dist_unit = 'kilometers'
        elev_unit = 'meters'
    return (speed_unit, dist_unit, elev_unit)

###########################################################################
# Flask definition                                                        #
###########################################################################
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/rider', methods=['GET', 'POST'])
def rider():
    res = get_rider_info(db_path)
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template('rider.html', rider=res[0], max_speed=res[4],
                           avg_speed=res[5], tot_dist=res[6], tot_climb=res[7],
                           speed_unit=speed_unit, dist_unit=dist_unit, elev_unit=elev_unit)


@app.route('/edit_rider', methods=['GET', 'POST'])
def edit_rider():
    res = get_rider_info(db_path)
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template('edit_rider.html', rider=res[0], units=res[1])


@app.route('/edit_rider_success', methods=['GET', 'POST'])
def edit_rider_success():
    if request.method == 'POST':
        res = get_rider_info(db_path)
        current_nm = res[0]
        nm = request.form.get('rider_name')
        units = request.form.get('units')
        if (nm in ['None', '']) or nm is None:
            nm = current_nm
        if (units in ['None', '']) or units is None:
            units = res[1]
        update_rider(current_nm, nm, units, db_path)
        return rider()


###########################################################################
# Run the app                                                             #
###########################################################################
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
