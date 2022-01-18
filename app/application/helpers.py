def num_pprint(s):
    return f'{s:,.2f}'


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


def convert_rider_info(units, max_speed, avg_speed, tot_dist, tot_climb):
    if units == 'imperial':
        max_speed = round(max_speed / 1.609, 2)
        avg_speed = round(avg_speed / 1.609, 2)
        tot_dist = round(tot_dist / 1.609, 2)
        tot_climb = round(tot_climb * 3.281, 2)
    else:
        max_speed = round(max_speed, 2)
        avg_speed = round(avg_speed, 2)
        tot_dist = round(tot_dist, 2)
        tot_climb = round(tot_climb, 2)
    return (num_pprint(s) for s in [max_speed, avg_speed, tot_dist, tot_climb])


def convert_summary_units(units, res, zeros=False):
    if units == 'imperial':
        try:
            dist = round(res[0] / 1.609, 2)
        except TypeError:
            dist = 0
        try:
            climb = round(res[3] * 3.281, 2)
        except TypeError:
            climb = 0
        try:
            mx_speed = round(res[6] / 1.609, 2)
        except TypeError:
            mx_speed = 0
    else:
        try:
            dist = round(res[0], 2)
        except TypeError:
            dist = 0
        try:
            climb = round(res[3], 2)
        except TypeError:
            climb = 0
        try:
            mx_speed = round(res[6], 2)
        except TypeError:
            mx_speed = 0
    try:
        mv_time = round(res[4], 1)
    except TypeError:
        mv_time = 0
    try:
        s_time = round(res[5], 1)
    except TypeError:
        s_time = 0
    try:
        cal = round(res[7], 2)
    except TypeError:
        cal = 0
    return (dist, res[1], res[2], climb, mv_time, s_time, mx_speed, cal)


def combine_res(n_all, n_virt):
    if n_virt is None:
        n_virt = 0
    if n_all is None:
        n_all = 0
    n_real = round(n_all - n_virt, 2)
    return (num_pprint(n_real), num_pprint(n_virt), num_pprint(n_all))


def summary_stats_combo(r_all, r_virt, u):
    r_all = convert_summary_units(u, r_all)
    r_virt = convert_summary_units(u, r_virt, zeros=True)
    out = dict()
    out['dist'] = combine_res(r_all[0], r_virt[0])
    try:
        out['min_dt'] = min([r_all[1], r_virt[1]])
        out['max_dt'] = max([r_all[2], r_virt[2]])
    except TypeError:
        out['min_dt'] = r_all[1]
        out['max_dt'] = r_all[2]
    out['elev'] = combine_res(r_all[3], r_virt[3])
    out['moving_time'] = combine_res(r_all[4], r_virt[4])
    out['elapsed_time'] = combine_res(r_all[5], r_virt[5])
    out['max_speed'] = (r_all[6], r_virt[6])
    out['cal'] = combine_res(r_all[7], r_virt[7])
    return out
