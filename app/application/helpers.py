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
