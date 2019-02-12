# modules
from stravalib.client import Client
import configparser

client = Client()

# Run this, then paste the resulting url into a browser
# I think it's only necessary to do this once...
url = client.authorization_url(client_id=10185,
                               redirect_uri='http://127.0.0.1:5000/authorization')

# the redirect will fail, but grab the new 'code' param from within the url

config = configparser.ConfigParser()
config.read('/home/bapfeld/strava/code/strava.ini')

code = config['Strava']['code']

token_response = client.exchange_code_for_token(client_id=10185, client_secret=config['Strava']['client_secret'], code=code)

access_token = token_response['access_token']
refresh_token = token_response['refresh_token']
expires_at = token_response['expires_at']

# Now store that short-lived access token somewhere (a database?)
client.access_token = access_token
# You must also store the refresh token to be used later on to obtain another valid access token 
# in case the current is already expired
client.refresh_token = refresh_token

# An access_token is only valid for 6 hours, store expires_at somewhere and
# check it before making an API call.
 
athlete = client.get_athlete()

# Get all activities:
activity_list = client.get_activities()
activity_id_list = [x.id for x in activity_list]

# Get a single activity
activity = client.get_activity(2122867341)

# Get the list of gear
g1 = client.get_gear('b3671458')
g1.name
g1.distance
