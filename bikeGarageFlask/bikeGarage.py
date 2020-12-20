import os
import datetime
import dateparser
import keyring
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, url_for
from stravalib.client import Client
# from wtforms import (Form, TextField, TextAreaField,
#                      validators, StringField, SubmitField)
from bikeGarage import database as db
from bikeGarage.strava_funcs import stravaConnection, generate_auth_url


###########################################################################
# Initial Setup                                                           #
###########################################################################
app = Flask(__name__)
load_dotenv(find_dotenv())
db_path = os.environ.get('STRAVA_DB_PATH')
schema_path = os.environ.get('SCHEMA_PATH')
client_id = os.environ.get('STRAVA_CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
app_code = keyring.get_password('bikeGarage', 'code')


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
    bike_list = db.get_all_bikes(db_path)
    return render_template('index.html', bike_menu_list=bike_list)


@app.route('/rider', methods=['GET', 'POST'])
def rider():
    res = db.get_rider_info(db_path)
    bike_list = db.get_all_bikes(db_path)
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template('rider.html', rider=res[0], max_speed=res[4],
                           avg_speed=res[5], tot_dist=res[6], tot_climb=res[7],
                           speed_unit=speed_unit, dist_unit=dist_unit,
                           elev_unit=elev_unit, bike_menu_list=bike_list)


@app.route('/edit_rider', methods=['GET', 'POST'])
def edit_rider():
    bike_list = db.get_all_bikes(db_path)
    if request.method == 'GET':
        res = db.get_rider_info(db_path)
        speed_unit, dist_unit, elev_unit = units_text(res[1])
        return render_template('edit_rider.html', rider=res[0], units=res[1],
                               bike_menu_list=bike_list)
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
    bike_list = db.get_all_bikes(db_path)
    if request.method == 'GET':
        if 'id' in request.args:
            b_id = request.args['id']
            bike_details = db.get_bike_details(db_path, b_id)
            return render_template('edit_bike.html', bike_details=bike_details,
                                   bike_menu_list=bike_list)
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
        else:
            purchase = dateparser.parse(purchase).strftime("%Y-%m-%d")
        if (price in ['None', '']) or price is None:
            price = bike_details[4]
        if (mfg in ['None', '']) or mfg is None:
            mfg = bike_details[1]
        db.update_bike(bike_details[0], nm, color, purchase, price,
                       mfg, db_path)
        return bike(bike_details[0])
        


@app.route('/edit_part', methods=['GET', 'POST'])
def edit_part():
    bike_list = db.get_all_bikes(db_path)
    if request.method == 'GET':
        if 'id' in request.args:
            p_id = request.args['id']
            part_details, b_id, b_nm = db.get_part_details(db_path, p_id)
            return render_template('edit_part.html', part_details=part_details,
                                   part_id=p_id, bike_name=b_nm,
                                   bike_menu_list=bike_list)
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
        virtual = request.form.get('virtual')
        if (p_type in ['None', '']) or p_type is None:
            p_type = part_details[1]
        if (added in ['None', '']) or added is None:
            added = part_details[2]
        else:
            added = dateparser.parse(added).strftime('%Y-%m-%d')
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
        if (virtual in ['None', '']) or virtual is None:
            virtual = part_details[10]
        else:
            virtual = int(virtual)
        db.update_part(p_id, p_type, added, brand, price, weight,
                       size, model, virtual, db_path)
        return part(p_id, edit=True)


@app.route('/bikes', methods=['GET', 'POST'])
def bikes():
    res = db.get_all_bikes(db_path)
    return render_template('bikes.html', bikes=res, bike_menu_list=res)


@app.route('/bike', methods=['GET', 'POST'])
def bike(b_id=None):
    rdr = db.get_rider_info(db_path)
    bike_list = db.get_all_bikes(db_path)
    if b_id is not None:
        start_date = None
        end_date = None
    elif request.method == 'GET':
        b_id = request.args['id']
        start_date = None
        end_date = None
    elif request.method == 'POST':
        b_id = request.form.get('bike_id')
        start_date = request.form.get('start_date')
        if start_date in ['None', '']:
            start_date = None
        else:
            start_date = dateparser.parse(start_date).strftime('%Y-%m-%d')
        end_date = request.form.get('end_date')
        if end_date in ['None', '']:
            end_date = None
        else:
            end_date = dateparser.parse(end_date).strftime('%Y-%m-%d')
    else:
        start_date = None
        end_date = None
    res = db.get_rider_info(db_path)
    deets = db.get_bike_details(db_path, b_id)
    parts = db.get_all_bike_parts(db_path, b_id)
    part_ids = [p[0] for p in parts]
    maint = db.get_maintenance(db_path, part_ids)
    stats = db.get_ride_data_for_bike(db_path, b_id, rdr[1],
                                      start_date, end_date)
    ms = max(stats['max_speed'])
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template('bike.html', parts=parts, bike_details=deets,
                           stats=stats, speed_unit=speed_unit, ms=ms,
                           dist_unit=dist_unit, elev_unit=elev_unit,
                           maint=maint, bike_menu_list=bike_list)


@app.route('/part', methods=['GET', 'POST'])
def part(p_id=None, end_date=None, start_date=None, edit=False):
    rdr = db.get_rider_info(db_path)
    bike_list = db.get_all_bikes(db_path)
    if request.method == 'GET':
        p_id = request.args['id']
    elif request.method == 'POST':
        if edit:
            pass
        else:
            p_id = request.form.get('part_id')
            start_date = request.form.get('start_date')
            if start_date in ['None', ''] or start_date is None:
                start_date = None
            else:
                start_date = dateparser.parse(start_date).strftime('%Y-%m-%d')
            end_date = request.form.get('end_date')
            if end_date in ['None', ''] or end_date is None:
                end_date = None
            else:
                end_date = dateparser.parse(end_date).strftime('%Y-%m-%d')
    part_details, b_id, b_nm = db.get_part_details(db_path, p_id)
    virt = bool(part_details[10] == 1)
    early_date = part_details[2]
    late_date = part_details[9]
    if (late_date in ['None', '']) or late_date is None:
        late_date = datetime.datetime.today().strftime("%Y-%m-%d")
    if end_date is not None:
        late_date = min([max([end_date, early_date]), late_date])
    if start_date is not None:
        early_date = max([min([start_date, late_date]), early_date])
    stats = db.get_ride_data_for_part(db_path, b_id, early_date, late_date,
                                      units=rdr[1])
    maint = db.get_maintenance(db_path, list(p_id))
    return render_template('part.html', bike_name=b_nm,
                           part_details=part_details, maint=maint,
                           stats=stats, bike_id=b_id, virtual=virt,
                           bike_menu_list=bike_list)


@app.route('/add_part', methods=['GET', 'POST'])
def add_part():
    bike_list = db.get_all_bikes(db_path)
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
                                   retired_part=retired_part,
                                   bike_menu_list=bike_list)
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
        return bike(bike)


@app.route('/add_bike', methods=['GET', 'POST'])
def add_bike():
    if request.method == 'GET':
        b_id = request.args['id']
        bike_list = db.get_all_bikes(db_path)
        return render_template('add_bike.html', bike_id=b_id,
                               bike_menu_list=bike_list)
    elif request.method == 'POST':
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
    bike_list = db.get_all_bikes(db_path)
    if request.method == 'GET':
        p_id = request.args['id']
        return render_template('add_maintenance.html', part_id=p_id, dt=dt,
                               bike_menu_list=bike_list)
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
    # get rider info
    res = db.get_rider_info(db_path)

    # run updater
    s = stravaConnection(client_id, client_secret, app_code, db_path, res)
    new_activities = s.fetch_new_activities()

    if new_activities is not None:
        db.add_multiple_rides(db_path, new_activities)
        msg = f'{len(new_activities)} new activities added!'
    else:
        msg = "No new activities found. Go ride your bike!"

    # check for new bikes
    db.find_new_bikes(db_path)

    return render_template('index.html', msg=msg)


@app.route('/part_averages', methods=['GET', 'POST'])
def part_averages():
    bike_list = db.get_all_bikes(db_path)
    avgs = db.get_part_averages(db_path)
    return render_template('part_averages.html', avgs=avgs,
                           bike_menu_list=bike_list)


@app.route('/strava_funcs', methods=['GET', 'POST'])
def strava_funcs():
    bike_list = db.get_all_bikes(db_path)
    auth_url = generate_auth_url(client_id)
    return render_template('strava_funcs.html', auth_url=auth_url,
                           bike_menu_list=bike_list)


@app.route('/strava_auth', methods=['GET'])
def strava_auth():
    code = request.args['code']
    keyring.set_password('bikeGarage', 'code', code)
    return render_template('index.html')


###########################################################################
# Run the app                                                             #
###########################################################################
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
