import sqlite3
import datetime
import requests
from stravalib.client import Client
from bikeGarage.database import get_all_ride_ids


def test_conn():
    try:
        _ = requests.get('http://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False


def reset_secrets(client, tkn, db_path, rider_name):
    client.access_token = tkn['access_token']
    client.refresh_token = tkn['refresh_token']
    client.expires_at = datetime.datetime.fromtimestamp(tkn['expires_at'])
    with sqlite3.connect(db_path) as conn:
        q = f"""UPDATE
                    riders
                SET
                    r_tkn='{client.refresh_token}',
                    tkn_exp={tkn['expires_at']}
                WHERE
                    name='{rider_name}';
             """
        c = conn.cursor()
        c.execute(q)


def gen_secrets(client, client_id, client_secret, code, db_path, rider_name):
    if client.refresh_token is None:
        tkn = client.exchange_code_for_token(client_id=client_id,
                                             client_secret=client_secret,
                                             code=code)
        reset_secrets(client, tkn, db_path, rider_name)
    elif datetime.datetime.now() > client.expires_at:
        tkn = client.refresh_access_token(client_id=client_id,
                                          client_secret=client_secret,
                                          refresh_token=client.refresh_token)
        reset_secrets(client, tkn, db_path, rider_name)
    else:
        pass


def fetch_new_activities(client, client_id, client_secret, code,
                         db_path, rider_name):
    id_list, max_dt = get_all_ride_ids(db_path, rider_name)
    if test_conn():
        gen_secrets(client, client_id, client_secret, code, db_path, rider_name)
        activity_list = client.get_activities(after=max_dt)
        if activity_list is not None:
            if id_list is not None:
                new_id_list = [x.id for x in activity_list
                               if (x.id not in id_list and x.type == "Ride")]
            else:
                new_id_list = [x.id for x in activity_list if x.type == 'Ride']
            if len(new_id_list) > 0:
                new_activities = [client.get_activity(id) for id
                                  in new_id_list]
            else:
                new_activities = None
        else:
            new_activities = None
    else:
        new_activities = None
    return new_activities
