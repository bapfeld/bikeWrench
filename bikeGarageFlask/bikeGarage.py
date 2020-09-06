import os
import datetime
import dateparser
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, url_for
from stravalib.client import Client
# from wtforms import (Form, TextField, TextAreaField,
#                      validators, StringField, SubmitField)
from bikeGarage import database as db
from bikeGarage.strava_funcs import fetch_new_activities


###########################################################################
# Initial Setup                                                           #
###########################################################################
app = Flask(__name__)
load_dotenv(find_dotenv())
db_path = os.environ.get('STRAVA_DB_PATH')
bdr = os.environ.get('BDR')
schema_path = os.environ.get('SCHEMA_PATH')
client_id = os.environ.get('STRAVA_CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
code = os.environ.get('STRAVA_APPLICATION_CODE')


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
                           speed_unit=speed_unit, dist_unit=dist_unit,
                           elev_unit=elev_unit)


@app.route('/edit_rider', methods=['GET', 'POST'])
def edit_rider():
    if request.method == 'GET':
        res = db.get_rider_info(db_path)
        speed_unit, dist_unit, elev_unit = units_text(res[1])
        return render_template('edit_rider.html', rider=res[0], units=res[1])
    elif request.method == 'POST':
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


@app.route('/edit_bike', methods=['GET', 'POST'])
def edit_bike():
    if request.method == 'GET':
        if 'id' in request.args:
            b_id = request.args['id']
            bike_details = db.get_bike_details(db_path, b_id)
            return render_template('edit_bike.html', bike_details=bike_details)
        else:
            return render_template('404.html')
    elif request.method == 'POST':
        bike_details = db.get_bike_details(db_path, request.form.get('id'))
        nm = request.form.get('bike_name')
        color = request.form.get('color')
        purchase = request.form.get('purchase')
        price = request.form.get('price')
        mfg = request.form.get('mfg')
        if (nm in ['None', '']) or nm is None:
            nm = bike_details[1]
        if (color in ['None', '']) or color is None:
            color = bike_details[2]
        if (purchase in ['None', '']) or purchase is None:
            purchase = bike_details[3]
        if (price in ['None', '']) or price is None:
            price = bike_details[4]
        if (mfg in ['None', '']) or mfg is None:
            mfg = bike_details[1]
        db.update_bike(bike_details[0], nm, color, purchase, price,
                       mfg, db_path)
        return bike(bike_detail[0])
        


@app.route('/edit_part', methods=['GET', 'POST'])
def edit_part():
    if request.method == 'GET':
        if 'id' in request.args:
            p_id = request.args['id']
            part_details, b_id, b_nm = db.get_part_details(db_path, p_id)
            return render_template('edit_part.html', part_details=part_details,
                                   part_id=p_id, bike_name=b_nm)
        else:
            return render_template('404.html')
    elif request.method == 'POST':
        p_id = request.form.get('id')
        part_details, b_id, b_nm = db.get_part_details(db_path, p_id)
        p_type = request.form.get('p_type')
        added = request.form.get('added')
        brand = request.form.get('brand')
        price = request.form.get('price')
        weight = request.form.get('weight')
        size = request.form.get('size')
        model = request.form.get('model')
        if (p_type in ['None', '']) or p_type is None:
            p_type = part_details[1]
        if (added in ['None', '']) or added is None:
            added = part_details[2]
        if (brand in ['None', '']) or brand is None:
            brand = part_details[3]
        if (price in ['None', '']) or price is None:
            price = part_details[4]
        if (weight in ['None', '']) or weight is None:
            weight = part_details[5]
        if (size in ['None', '']) or size is None:
            size = part_details[6]
        if (model in ['None', '']) or model is None:
            model = part_details[7]
        db.update_part(p_id, p_type, added, brand, price, weight,
                       size, model, db_path)
        return part(p_id)


@app.route('/bikes', methods=['GET', 'POST'])
def bikes():
    res = db.get_all_bikes(db_path)
    return render_template('bikes.html', bikes=res)


@app.route('/bike', methods=['GET', 'POST'])
def bike(b_id=None):
    if 'id' in request.args:
        b_id = request.args['id']
    res = db.get_rider_info(db_path)
    deets = db.get_bike_details(db_path, b_id)
    parts = db.get_all_bike_parts(db_path, b_id)
    part_ids = [p[0] for p in parts]
    maint = db.get_maintenance(db_path, part_ids)
    stats = db.get_ride_data_for_bike(db_path, b_id)
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template('bike.html', parts=parts, bike_details=deets,
                           stats=stats, speed_unit=speed_unit,
                           dist_unit=dist_unit, elev_unit=elev_unit,
                           maint=maint)


@app.route('/part', methods=['GET', 'POST'])
def part(p_id=None):
    if 'id' in request.args:
        p_id = request.args['id']
    part_details, b_id, b_nm = db.get_part_details(db_path, p_id)
    early_date = part_details[2]
    late_date = part_details[9]
    if (late_date in ['None', '']) or late_date is None:
        late_date = datetime.datetime.today().strftime("%Y-%m-%d")
    stats = db.get_ride_data_for_part(db_path, b_id, early_date, late_date)
    maint = db.get_maintenance(db_path, list(p_id))
    return render_template('part.html', bike_name=b_nm,
                           part_details=part_details, maint=maint,
                           stats=stats, bike_id=b_id)


@app.route('/add_part', methods=['GET', 'POST'])
def add_part():
    if request.method == 'GET':
        if 'bike_id' in request.args:
            b_id = request.args['bike_id']
            try:
                part_type = request.args['tp']
                if part_type in ['None', '']:
                    part_type = None
            except:
                part_type = None
            try:
                brand = request.args['brand']
                if brand in ['None', '']:
                    brand = None
            except:
                brand = None
            try:
                weight = request.args['weight']
                if weight in ['None', '']:
                    weight = None
            except:
                weight = None
            try:
                size = request.args['size']
                if size in ['None', '']:
                    size = None
            except:
                size = None
            try:
                model = request.args['model']
                if model in ['None', '']:
                    model = None
            except:
                model = None
            try:
                retire = int(request.args['retire'])
                retired_part = request.args['part_id']
            except:
                retire = 0
                retired_part = None
            added = datetime.datetime.today().strftime('%Y-%m-%d')
            return render_template('add_part.html', bike_id=b_id,
                                   part_type=part_type, brand=brand, weight=weight,
                                   size=size, model=model, added=added, retire=retire,
                                   retired_part=retired_part)
        else:
            return render_template('404.html')
    elif request.method == 'POST':
        retire = request.form.get('retire')
        retired_part = request.form.get('retired_part')
        part_type = request.form.get('p_type')
        if part_type in ['None', '']:
            part_type = None
        added = request.form.get('added')
        if added in ['None', '']:
            added = None
        else:
            added = dateparser.parse(added)
        brand = request.form.get('brand')
        if brand in ['None', '']:
            brand = None
        price = request.form.get('price')
        if price in ['None', '']:
            price = None
        weight = request.form.get('weight')
        if weight in ['None', '']:
            weight = None
        size = request.form.get('size')
        if size in ['None', '']:
            size = None
        model = request.form.get('model')
        if model in ['None', '']:
            model = None
        bike = request.form.get('bike_id')
        if bike in ['None', '']:
            bike = None
        vals = (part_type, added, brand, price, weight, size,
                model, bike, 'TRUE')
        db.add_part(db_path, vals)
        if int(retire) == 1:
            db.retire(db_path, retired_part, added)
        return bikes()


@app.route('/add_bike', methods=['GET', 'POST'])
def add_bike():
    if request.method == 'POST':
        b_id = request.args['id']
        return render_template('add_bike.html', bike_id=b_id)


@app.route('/add_bike_success', methods=['GET', 'POST'])
def add_bike_success():
    if request.method == 'POST':
        nm = request.form.get('nm')
        if nm in ['None', '']:
            nm = None
        color = request.form.get('color')
        if color in ['None', '']:
            color = None
        purchase = request.form.get('purchase')
        if purchase in ['None', '']:
            purchase = None
        else:
            purchase = dateparser.parse(purchase)
        mfg = request.form.get('mfg')
        if mfg in ['None', '']:
            mfg = None
        price = request.form.get('price')
        if price in ['None', '']:
            price = None
        b_id = request.form.get('bike_id')
        if b_id in ['None', '']:
            b_id = None
        db.add_new_bike(db_path, b_id, nm, color, purchase, price, mfg)
        return bikes()


@app.route('/add_maintenance', methods=['GET', 'POST'])
def add_maintenance():
    dt = datetime.datetime.today().strftime('%Y-%m-%d')
    if request.method == 'GET':
        p_id = request.args['id']
        return render_template('add_maintenance.html', part_id=p_id, dt=dt)
    elif request.method == 'POST':
        p_id = request.form.get('p_id')
        new_dt = request.form.get('dt')
        work = request.form.get('work')
        if new_dt in ['None', '']:
            new_dt = dt
        else:
            new_dt = dateparser.parse(new_dt)
        if work in ['None', '']:
            work = None
        db.add_maintenance(db_path, p_id, work, new_dt)
        return part(p_id)


@app.route('/fetch_rides', methods=['GET'])
def fetch_rides():
    # establish client
    cl = Client()

    # get rider info
    res = db.get_rider_info(db_path)
    cl.refresh_token = res[2]
    cl.expires_at = res[3]

    # run updater
    new_activities = fetch_new_activities(cl, client_id, client_secret,
                                          code, db_path, res[0])
    if new_activities is not None:
        db.add_multiple_rides(db_path, new_activities)

    # check for new bikes
    db.find_new_bikes(db_path)

    return render_template('index.html')


@app.route('/part_averages', methods=['GET', 'POST'])
def part_averages():
    avgs = db.get_part_averages(db_path)
    return render_template('part_averages.html', avgs=avgs)


###########################################################################
# Run the app                                                             #
###########################################################################
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
