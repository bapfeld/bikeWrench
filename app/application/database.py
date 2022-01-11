import datetime
import dateparser
from stravalib import unithelper
from sqlalchemy import func
from .models import db, Riders, Bikes, Rides, Parts, Maintenance
from .helpers import (convert_rider_info, convert_summary_units,
                      combine_res, summary_stats_combo)


def get_rider_info():
    rider = Riders.query.first()
    rider_name = rider.name
    units = rider.units
    if rider.r_tkn is not None:
        refresh_token = rider.r_tkn
        expires_at = datetime.datetime.fromtimestamp(rider.tkn_exp)
    else:
        refresh_token = None
        expires_at = None
    try:
        max_speed = round(db.session.query(func.max(Rides.max_speed)).scalar(), 2)
    except:
        max_speed = 0
    try:
        avg_speed = round(db.session.query(func.avg(Rides.avg_speed)).scalar(), 2)
    except:
        avg_speed = 0
    try:
        tot_dist = round(db.session.query(func.sum(Rides.distance)).scalar(), 2)
    except:
        tot_dist = 0
    try:
        tot_climb = round(db.session.query(func.sum(Rides.elev)).scalar(), 2)
    except:
        tot_climb = 0    
    max_speed, avg_speed, tot_dist, tot_climb = convert_rider_info(units,
                                                                   max_speed,
                                                                   avg_speed,
                                                                   tot_dist,
                                                                   tot_climb)
    return (rider_name, units, refresh_token, expires_at,
            max_speed, avg_speed, tot_dist, tot_climb)


def update_rider(current_nm, nm, units):
    (db.session
     .query(Riders)
     .filter(Riders.name == current_nm)
     .update({Riders.name: nm,
              Riders.units: units})
     )
    db.session.commit()


def update_bike(b_id, nm, color, purchase, price, mfg):
    (db.session
     .query(Bikes)
     .filter(Bikes.bike_id == b_id)
     .update({Bikes.name: nm,
              Bikes.color: color,
              Bikes.purchased: purchase,
              Bikes.price: price,
              Bikes.mfg: mfg}))
    db.session.commit()


def update_part(p_id, p_type, added, brand, price, weight,
                size, model, virtual):
    (db.session
     .query(Parts)
     .filter(Parts.part_id == p_id)
     .update({tp: p_type,
              added: added,
              brand: brand,
              price: price,
              weight: weight,
              size: size,
              model: model,
              virtual: virtual}))
    db.session.commit()


def get_all_bikes():
    bikes = Bikes.query.all()
    return bikes


def get_bike_details(bike_id):
    bike_details = Bikes.query.filter(Bikes.bike_id == bike_id).first()
    return bike_details


def get_all_ride_ids():
    rides = Rides.query(Rides.ride_id).all()
    if len(rides) > 0:
        max_dt = dateparser.parse(db.session.query(func.max(Rides.date)).first())
        max_dt = max_dt - datetime.timedelta(days=1)
        max_dt = max_dt.strftime('%Y-%m-%d')
    else:
        max_dt = None
    return (rides, max_dt)


def add_part(part_values):
    tp, added, brand, price, weight, size, model, b_id, virtual = part_values
    new_part = Parts(tp=tp,
                     added=added,
                     brand=brand,
                     price=price,
                     weight=weight,
                     size=size,
                     model=model,
                     b_id=b_id,
                     virtual=virtual)
    db.session.add(new_part)
    db.session.commit()


def get_all_bike_parts(current_bike):
    current_bike_parts_list = (Parts
                               .query
                               .filter(Parts.bike == current_bike)
                               .filter(Parts.retired is None)
                               .all())
    return current_bike_parts_list


def get_maintenance(part_ids):
    m = (db.session.query(Maintenance)
         .filter(Maintenance.part.in_(part_ids))
         .order_by(Maintenance.date.desc())
         .all())
    return m


def get_all_ride_data():
    all_rides = Rides.query.all()
    return all_rides


def get_ride_data_for_bike(bike_id, units, start_date=None,
                           end_date=None):
    query = (db.session
             .query(func.sum(Rides.distance).label('dist'),
                    func.min(Rides.date).label('earliest_ride'),
                    func.max(Rides.date).label('recent_ride'),
                    func.sum(Rides.elev).label('climb'),
                    func.sum(Rides.moving_time).label('mov_saddle_time'),
                    func.sum(Rides.elapsed_time).label('saddle_time'),
                    func.max(Rides.max_speed).label('max_speed'),
                    func.sum(Rides.calories).label('calories'))
             .filter(Rides.bike == bike_id)
             )
    q_virt = query.filter(Rides.tp == 'VirtualRide')
    if start_date is not None:
        query = query.filter(Rides.date >= start_date)
        q_virt = q_virt.filter(Rides.date >= start_date)
    if end_date is not None:
        query = query.filter(Rides.date <= end_date)
        q_virt = q_virt.filter(Rides.date <= end_date)
    res_all = query.first()
    res_virt = q_virt.first()
    res_out = summary_stats_combo(res_all, res_virt, units)
    return res_out


def get_ride_data_for_part(bike_id, units, early_date, late_date):
    query = (db.session
             .query(func.sum(Rides.dist).label('dist'),
                    func.min(Rides.date).label('earliest_date'),
                    func.max(Rides.date).label('recent_ride'),
                    func.sum(Rides.elev).label('climb'),
                    func.sum(Rides.moving_time).label('mov_saddle_time'),
                    func.sum(Rides.elapsed_time).label('saddle_time'),
                    func.max(Rides.max_speed).label('max_speed'),
                    func.sum(Rides.calories).label('calories'))
             .filter(and_(Rides.bike == bike_id,
                          Rides.date >= early_date,
                          Rides.date <= late_date))
             )
    q_virt = query.filter(Rides.tp == 'VirtualRide')
    res_all = query.first()
    res_virt = q_virt.first()
    res_out = summary_stats_combo(res_all, res_virt, units)
    return res_out


def add_multiple_rides(activity_list):
    def gear_try(x):
        try:
            out = x.gear.id
        except AttributeError:
            out = 'Unknown'
        return out

    def unit_try(num, t):
        if t == 'long_dist':
            return float(unithelper.kilometers(num))
        elif t == 'short_dist':
            return float(unithelper.meters(num))
        elif t == 'speed':
            return float(unithelper.kph(num))
    a_list = [Rides(ride_id=a.id,
                    bike=gear_try(a),
                    distance=unit_try(a.distance, 'long_dist'),
                    name=a.name,
                    date=a.start_date.strftime("%Y-%m-%d"),
                    moving_time=a.moving_time.seconds / 3600,
                    elapsed_time=a.elapsed_time.seconds / 3600,
                    elev=unit_try(a.total_elevation_gain, 'short_dist'),
                    tp=a.type,
                    avg_speed=unit_try(a.average_speed, 'speed'),
                    max_speed=unit_try(a.max_speed, 'speed'),
                    calories=float(a.calories))
              for a in activity_list]

    db.session.add_all(a_list)
    db.session.commit()


def add_new_bike(bike_id, bike_name, bike_color,
                 bike_purchase, bike_price, bike_mfg):
    new_bike = Bikes(bike_id=bike_id,
                     name=bike_name,
                     color=bike_color,
                     purchased=bike_purchase,
                     price=bike_price,
                     mfg=bike_mfg)
    db.session.add(new_bike)
    db.session.commit()


def add_maintenance(part_id, work, dt):
    new_maint = Maintenance(part=part_id,
                            work=work,
                            date=dt)
    db.session.add(new_maint)
    db.session.commit()


def find_new_bikes():
    """Simple function to determine if there are any bikes
       that haven't been added
     """

    all_bike_ids = get_all_bike_ids(db_path)
    res = db.session.query(Rides.bike).distinct().all()
    new_bikes = [x for x in res if x not in all_bike_ids]
    if len(new_bikes) > 0:
        b_list = [Bikes(bike_id=b,
                        name=f'tmp_nm_{b}')
                  for b in new_bikes]
        db.session.add_all(b_list)
        db.session.commit()


def get_part_details(part_id):
    res = Parts.query.filter(Parts.part_id == part_id).first()
    b_id, b_nm = (Bikes
                  .query(Bikes.bike_id, Bikes.name)
                  .filter(Bikes.bike_id == res.bike)
                  .first())
    
    return (res, b_id, b_nm)


def get_part_averages():
    averages = (db.session
                .query(Parts.tp,
                       func.avg(Parts.price),
                       func.avg(Parts.weight),
                       func.avg(Parts.dist),
                       func.avg(Parts.elev),
                       func.avg(Parts.retired - Parts.added))
                .filter(Parts.retired == 1)
                .group_by(Parts.tp)
                .all())
    return averages

