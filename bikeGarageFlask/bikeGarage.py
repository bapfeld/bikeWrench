import os
import sqlite3
import datetime
import dateparser
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, url_for
# from wtforms import (Form, TextField, TextAreaField,
#                      validators, StringField, SubmitField)
from bikeGarage import database as db


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
    res = db.get_rider_info(db_path)
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template('rider.html', rider=res[0], max_speed=res[4],
                           avg_speed=res[5], tot_dist=res[6], tot_climb=res[7],
                           speed_unit=speed_unit, dist_unit=dist_unit, elev_unit=elev_unit)


@app.route('/edit_rider', methods=['GET', 'POST'])
def edit_rider():
    res = db.get_rider_info(db_path)
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template('edit_rider.html', rider=res[0], units=res[1])


@app.route('/edit_rider_success', methods=['GET', 'POST'])
def edit_rider_success():
    if request.method == 'POST':
        res = db.get_rider_info(db_path)
        current_nm = res[0]
        nm = request.form.get('rider_name')
        units = request.form.get('units')
        if (nm in ['None', '']) or nm is None:
            nm = current_nm
        if (units in ['None', '']) or units is None:
            units = res[1]
        db.update_rider(current_nm, nm, units, db_path)
        return rider()


@app.route('/bikes', methods=['GET', 'POST'])
def bikes():
    res = db.get_all_bikes(db_path)
    return render_template('bikes.html', bikes=res)


@app.route('/bike', methods=['GET', 'POST'])
def bike():
    if 'id' in request.args:
        res = db.get_rider_info(db_path)
        b_id = request.args['id']
        deets = db.get_bike_details(db_path, b_id)
        parts = db.get_all_bike_parts(db_path, b_id)
        part_ids = [p[0] for p in parts]
        maint = db.get_maintenance(db_path, part_ids)
        stats = db.get_ride_data_for_bike(db_path, b_id)
        speed_unit, dist_unit, elev_unit = units_text(res[1])
        return render_template('bike.html', parts=parts, bike_details=deets,
                               stats=stats, speed_unit=speed_unit, dist_unit=dist_unit,
                               elev_unit=elev_unit, maint=maint)


@app.route('/part', methods=['GET', 'POST'])
def part():
    if 'id' in request.args:
        p_id = request.args['id']
        part_details, b_id, b_nm = db.get_part_details(db_path, p_id)
        early_date = part_details[2]
        stats = db.get_ride_data_for_part(db_path, b_id, early_date)
        maint = db.get_maintenance(db_path, list(p_id))
        return render_template('part.html', bike_name=b_nm, part_details=part_details,
                               maint=maint, stats=stats)


###########################################################################
# Run the app                                                             #
###########################################################################
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
