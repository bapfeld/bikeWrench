import datetime
import dateparser
import keyring
from flask import Flask, render_template, request, url_for, make_response
from flask import current_app as app
from . import database as dtb
from .strava_funcs import stravaConnection, generate_auth_url
from .forms import PartForm, MaintenanceForm, BikeForm, DateLimitForm, RiderForm
from .helpers import units_text
from .models import db, Riders, Bikes, Rides, Parts, Maintenance


###########################################################################
# Flask definition                                                        #
###########################################################################
@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
@app.route("/home", methods=["GET"])
def index():
    bike_list = dtb.get_all_bikes()
    return render_template("index.html", bike_menu_list=bike_list)


@app.route("/rider", methods=["GET", "POST"])
def rider():
    res = dtb.get_rider_info()
    bike_list = dtb.get_all_bikes()
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template(
        "rider.html",
        rider=res[0],
        max_speed=res[4],
        avg_speed=res[5],
        tot_dist=res[6],
        tot_climb=res[7],
        speed_unit=speed_unit,
        dist_unit=dist_unit,
        elev_unit=elev_unit,
        bike_menu_list=bike_list,
    )


@app.route("/edit_rider", methods=["GET", "POST"])
def edit_rider():
    bike_list = dtb.get_all_bikes()
    res = dtb.get_rider_info()
    fm = RiderForm(rider=res[0], units=res[1])
    if fm.validate_on_submit():
        current_nm = res[0]
        nm = request.form.get("rider")
        units = request.form.get("units")
        if (nm in ["None", ""]) or nm is None:
            nm = current_nm
        if (units in ["None", ""]) or units is None:
            units = res[1]
        dtb.update_rider(current_nm, nm, units)
        return rider()
    else:
        speed_unit, dist_unit, elev_unit = units_text(res[1])
        return render_template(
            "edit_rider.html",
            rider=res[0],
            units=res[1],
            bike_menu_list=bike_list,
            form=fm,
        )


@app.route("/edit_bike", methods=["GET", "POST"])
def edit_bike():
    bike_list = dtb.get_all_bikes()
    fm = BikeForm(edit=True)
    if fm.validate_on_submit():
        bike_details = dtb.get_bike_details(request.args["bike_id"])
        nm = request.form.get("bike_name")
        color = request.form.get("color")
        purchase = request.form.get("purchase")
        price = request.form.get("price")
        mfg = request.form.get("mfg")
        if (nm in ["None", ""]) or nm is None:
            nm = bike_details.name
        if (color in ["None", ""]) or color is None:
            color = bike_details.color
        if (purchase in ["None", ""]) or purchase is None:
            purchase = bike_details.purchased
        else:
            purchase = dateparser.parse(purchase)
        if (price in ["None", ""]) or price is None:
            price = bike_details.price
        if (mfg in ["None", ""]) or mfg is None:
            mfg = bike_details.mfg
        dtb.update_bike(bike_details.bike_id, nm, color, purchase, price, mfg)
        return bike(bike_details.bike_id)
    else:
        if "id" in request.args:
            b_id = request.args["id"]
            bike_details = dtb.get_bike_details(b_id)
            fm_with_defaults = BikeForm(
                edit=True,
                nm=bike_details.name,
                color=bike_details.color,
                purchase=bike_details.purchased,
                mfg=bike_details.mfg,
                price=bike_details.price,
            )
            return render_template(
                "edit_bike.html",
                bike_details=bike_details,
                bike_menu_list=bike_list,
                form=fm_with_defaults,
            )
        else:
            return render_template("404.html")


@app.route("/edit_part", methods=["GET", "POST"])
def edit_part():
    bike_list = dtb.get_all_bikes()
    fm = PartForm(edit=True)
    if fm.validate_on_submit():
        p_id = request.args["part_id"]
        part_details, b_id, b_nm = dtb.get_part_details(p_id)
        p_type = request.form.get("p_type")
        added = request.form.get("added")
        brand = request.form.get("brand")
        price = request.form.get("price")
        weight = request.form.get("weight")
        size = request.form.get("size")
        model = request.form.get("model")
        virtual = request.form.get("virtual")
        if (p_type in ["None", ""]) or p_type is None:
            p_type = part_details.tp
        if (added in ["None", ""]) or added is None:
            added = part_details.added
        else:
            added = dateparser.parse(added).strftime("%Y-%m-%d")
        if (brand in ["None", ""]) or brand is None:
            brand = part_details.brand
        if (price in ["None", ""]) or price is None:
            price = None
        if (weight in ["None", ""]) or weight is None:
            weight = None
        if (size in ["None", ""]) or size is None:
            size = part_details.size
        if (model in ["None", ""]) or model is None:
            model = part_details.model
        if (virtual in ["None", ""]) or virtual is None:
            virtual = 0
        else:
            virtual = int(virtual)
        dtb.update_part(p_id, p_type, added, brand, price, weight, size, model, virtual)
        return part(p_id, edit=True)
    else:
        if "part_id" in request.args:
            p_id = request.args["part_id"]
            part_details, b_id, b_nm = dtb.get_part_details(p_id)
            fm_with_defaults = PartForm(
                edit=True,
                p_type=part_details.tp,
                dt=part_details.added,
                brand=part_details.brand,
                price=part_details.price,
                weight=part_details.weight,
                size=part_details.size,
                model=part_details.model,
                virt=part_details.virtual,
            )
            return render_template(
                "edit_part.html",
                part_details=part_details,
                part_id=p_id,
                bike_name=b_nm,
                bike_menu_list=bike_list,
                form=fm_with_defaults,
            )
        else:
            return render_template("404.html")


@app.route("/bikes", methods=["GET", "POST"])
def bikes():
    res = dtb.get_all_bikes()
    return render_template("bikes.html", bikes=res, bike_menu_list=res)


@app.route("/bike", methods=["GET", "POST"])
def bike(b_id=None):
    rdr = dtb.get_rider_info()
    bike_list = dtb.get_all_bikes()
    fm = DateLimitForm()
    if fm.validate_on_submit():
        b_id = request.args["bike_id"]
        start_date = request.form.get("start_date")
        if start_date in ["None", ""] or start_date is None:
            start_date = None
        else:
            start_date = dateparser.parse(start_date).strftime("%Y-%m-%d")
        end_date = request.form.get("end_date")
        if end_date in ["None", ""] or end_date is None:
            end_date = None
        else:
            end_date = dateparser.parse(end_date).strftime("%Y-%m-%d")
    else:
        b_id = request.args["id"]
        start_date = None
        end_date = None
    res = dtb.get_rider_info()
    deets = dtb.get_bike_details(b_id)
    parts = dtb.get_all_bike_parts(b_id)
    part_ids = [p.part_id for p in parts]
    maint = dtb.get_maintenance(part_ids)
    stats = dtb.get_ride_data_for_bike(b_id, rdr[1], start_date, end_date)
    print(stats)
    ms = max(stats["max_speed"])
    speed_unit, dist_unit, elev_unit = units_text(res[1])
    return render_template(
        "bike.html",
        parts=parts,
        bike_details=deets,
        stats=stats,
        speed_unit=speed_unit,
        ms=ms,
        dist_unit=dist_unit,
        elev_unit=elev_unit,
        maint=maint,
        bike_menu_list=bike_list,
        form=fm,
    )


@app.route("/part", methods=["GET", "POST"])
def part(p_id=None, end_date=None, start_date=None, edit=False):
    rdr = dtb.get_rider_info()
    bike_list = dtb.get_all_bikes()
    fm = DateLimitForm()
    if fm.validate_on_submit():
        if edit:
            pass
        else:
            p_id = request.args["part_id"]
            start_date = request.form.get("start_date")
            if start_date in ["None", ""] or start_date is None:
                start_date = None
            else:
                start_date = dateparser.parse(start_date).strftime("%Y-%m-%d")
            end_date = request.form.get("end_date")
            if end_date in ["None", ""] or end_date is None:
                end_date = None
            else:
                end_date = dateparser.parse(end_date).strftime("%Y-%m-%d")
    else:
        p_id = request.args["part_id"]

    part_details, b_id, b_nm = dtb.get_part_details(p_id)
    virt = bool(part_details.virtual == 1)
    early_date = part_details.added
    late_date = part_details.retired
    if (late_date in ["None", ""]) or late_date is None:
        late_date = datetime.datetime.today().strftime("%Y-%m-%d")
    if end_date is not None:
        late_date = min([max([end_date, early_date]), late_date])
    if start_date is not None:
        early_date = max([min([start_date, late_date]), early_date])
    stats = dtb.get_ride_data_for_part(
        b_id, units=rdr[1], early_date=early_date, late_date=late_date
    )
    maint = dtb.get_maintenance(tuple(p_id))
    return render_template(
        "part.html",
        bike_name=b_nm,
        part_details=part_details,
        maint=maint,
        stats=stats,
        bike_id=b_id,
        virtual=virt,
        bike_menu_list=bike_list,
        form=fm,
    )


@app.route("/add_part", methods=["GET", "POST"])
def add_part():
    bike_list = dtb.get_all_bikes()
    fm = PartForm()
    if fm.validate_on_submit():
        part_type = request.form.get("p_type")
        b_id = request.args["bike_id"]
        if part_type in ["None", ""]:
            part_type = None
        added = request.form.get("dt")
        if added in ["None", ""]:
            added = None
        else:
            added = dateparser.parse(added)
        brand = request.form.get("brand")
        if brand in ["None", ""]:
            brand = None
        price = request.form.get("price")
        if price in ["None", ""]:
            price = None
        weight = request.form.get("weight")
        if weight in ["None", ""]:
            weight = None
        size = request.form.get("size")
        if size in ["None", ""]:
            size = None
        model = request.form.get("model")
        if model in ["None", ""]:
            model = None
        virtual = request.form.get("virt")
        if virtual in ["0", 0]:
            virtual = 0
        else:
            virtual = 1
        vals = (part_type, added, brand, price, weight, size, model, b_id, virtual)
        dtb.add_part(vals)
        return bike(b_id)
    else:
        b_id = request.args["bike_id"]
        try:
            part_type = request.args["tp"]
            if part_type in ["None", ""]:
                part_type = None
        except:
            part_type = None
        try:
            brand = request.args["brand"]
            if brand in ["None", ""]:
                brand = None
        except:
            brand = None
        try:
            weight = request.args["weight"]
            if weight in ["None", ""]:
                weight = None
        except:
            weight = None
        try:
            size = request.args["size"]
            if size in ["None", ""]:
                size = None
        except:
            size = None
        try:
            model = request.args["model"]
            if model in ["None", ""]:
                model = None
        except:
            model = None
        try:
            virt = int(request.args["virtual"])
        except:
            virt = 0
        added = datetime.datetime.today().strftime("%Y-%m-%d")
        return render_template(
            "add_part.html",
            bike_id=b_id,
            part_type=part_type,
            brand=brand,
            weight=weight,
            size=size,
            model=model,
            added=added,
            bike_menu_list=bike_list,
            virtual=virt,
            form=fm,
        )


@app.route("/add_bike", methods=["GET", "POST"])
def add_bike():
    fm = BikeForm()
    if fm.validate_on_submit():
        nm = request.form.get("nm")
        if nm in ["None", ""]:
            nm = None
        color = request.form.get("color")
        if color in ["None", ""]:
            color = None
        purchase = request.form.get("purchase")
        if purchase in ["None", ""]:
            purchase = None
        else:
            purchase = dateparser.parse(purchase)
        mfg = request.form.get("mfg")
        if mfg in ["None", ""]:
            mfg = None
        price = request.form.get("price")
        if price in ["None", ""]:
            price = None
        b_id = request.form.get("bike_id")
        if b_id in ["None", ""]:
            b_id = None
        dtb.add_new_bike(b_id, nm, color, purchase, price, mfg)
        return bikes()
    else:
        b_id = request.args["id"]
        bike_list = dtb.get_all_bikes()
        return render_template(
            "add_bike.html", bike_id=b_id, bike_menu_list=bike_list, form=fm
        )


@app.route("/add_maintenance", methods=["GET", "POST"])
def add_maintenance():
    dt = datetime.datetime.today().strftime("%Y-%m-%d")
    bike_list = dtb.get_all_bikes()
    fm = MaintenanceForm()
    if fm.validate_on_submit():
        p_id = request.args["part_id"]
        new_dt = request.form.get("dt")
        work = request.form.get("work")
        if new_dt in ["None", ""]:
            new_dt = dt
        else:
            new_dt = dateparser.parse(new_dt)
        if work in ["None", ""]:
            work = None
        dtb.add_maintenance(p_id, work, new_dt)
        return part(p_id)
    else:
        p_id = request.args["part_id"]
        return render_template(
            "add_maintenance.html",
            part_id=p_id,
            dt=dt,
            bike_menu_list=bike_list,
            form=fm,
        )


@app.route("/fetch_rides", methods=["GET"])
def fetch_rides():
    # get rider info
    res = dtb.get_rider_info()

    # run updater
    s = stravaConnection(
        app.config["CLIENT_ID"],
        app.config["CLIENT_SECRET"],
        app.config["APP_CODE"],
        res,
    )
    new_activities = s.fetch_new_activities()

    if new_activities is not None:
        dtb.add_multiple_rides(new_activities)
        msg = f"{len(new_activities)} new activities added!"
    else:
        msg = "No new activities found. Go ride your bike!"

    # check for new bikes
    dtb.find_new_bikes()

    return render_template("index.html", msg=msg)


@app.route("/part_averages", methods=["GET", "POST"])
def part_averages():
    bike_list = dtb.get_all_bikes()
    avgs = dtb.get_part_averages()
    return render_template("part_averages.html", avgs=avgs, bike_menu_list=bike_list)


@app.route("/strava_funcs", methods=["GET", "POST"])
def strava_funcs():
    bike_list = dtb.get_all_bikes()
    auth_url = generate_auth_url(app.config["CLIENT_ID"])
    return render_template(
        "strava_funcs.html", auth_url=auth_url, bike_menu_list=bike_list
    )


@app.route("/strava_auth", methods=["GET"])
def strava_auth():
    code = request.args["code"]
    keyring.set_password("bikeWrench", "code", code)
    return render_template("index.html")


@app.errorhandler(404)
def not_found():
    """Page not found."""
    return make_response(render_template("404.html"), 404)
