import sqlite3
import datetime
import requests
from stravalib.client import Client
from .database import get_all_ride_ids


class stravaConnection():
    def __init__(self, client_id, client_secret, code, db_path, rider_info):
        self.cl = Client()
        self.client_id = client_id
        self.client_secret = client_secret
        self.code = code
        self.db_path = db_path
        self.rider_name = rider_info[0]
        self.tkn = None
        self.activity_list = None
        self.cl.refresh_token = rider_info[2]
        self.cl.expires_at = rider_info[3]
        self.ride_types = ['Ride', 'VirtualRide']

    def test_conn(self):
        try:
            _ = requests.get('http://www.google.com', timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def reset_secrets(self):
        self.cl.access_token = self.tkn['access_token']
        self.cl.refresh_token = self.tkn['refresh_token']
        self.cl.expires_at = datetime.datetime.fromtimestamp(self.tkn['expires_at'])
        with sqlite3.connect(self.db_path) as conn:
            q = f"""UPDATE
                        riders
                    SET
                        r_tkn='{self.cl.refresh_token}',
                        tkn_exp={self.tkn['expires_at']}
                    WHERE
                        name='{self.rider_name}';
                 """
            c = conn.cursor()
            c.execute(q)

    def gen_secrets(self):
        if self.cl.refresh_token is None:
            self.tkn = self.cl.exchange_code_for_token(client_id=self.client_id,
                                                       client_secret=self.client_secret,
                                                       code=self.code)
            self.reset_secrets()
        else:
            self.tkn = self.cl.refresh_access_token(client_id=self.client_id,
                                                    client_secret=self.client_secret,
                                                    refresh_token=self.cl.refresh_token)
            self.reset_secrets()

    def fetch_new_activities(self, recent_only=True):
        id_list, max_dt = get_all_ride_ids(self.db_path)
        if self.test_conn():
            self.gen_secrets()
            if recent_only:
                self.activity_list = self.cl.get_activities(after=max_dt)
            else:
                self.activity_list = self.cl.get_activities()
            if self.activity_list is not None:
                if id_list is not None:
                    new_id_list = [x.id for x in self.activity_list
                                   if (x.id not in id_list
                                       and x.type in self.ride_types)]
                else:
                    new_id_list = [x.id for x in self.activity_list
                                   if x.type in self.ride_types]
                if len(new_id_list) > 0:
                    new_activities = [self.cl.get_activity(id) for id
                                      in new_id_list]
                else:
                    new_activities = None
            else:
                new_activities = None
        else:
            new_activities = None
        return new_activities


def generate_auth_url(client_id):
    client = Client()
    url = client.authorization_url(client_id=client_id,
                                   redirect_uri='http://127.0.0.1:5002/strava_auth',
                                   scope=['read', 'read_all', 'activity:read_all',
                                          'profile:read_all'])
    return url
