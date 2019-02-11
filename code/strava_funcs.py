# modules
import time
import swagger_client, configparser, os
from swagger_client.rest import ApiException
from pprint import pprint

# get session set up
# Configure OAuth2 access token for authorization: strava_oauth
config = configparser.ConfigParser()
cpfp = os.path.expanduser('~/strava/code/config_path.txt')
with open(cpfp, 'r') as my_path:
    cpath = my_path.readline()
    cpath = cpath.rstrip()
config.read(cpath)

my_access_token = config['strava']['access_token']
swagger_client.configuration.access_token = my_access_token

# create an instance of the API class
api_instance = swagger_client.ActivitiesApi()

before = 56 # Integer | An epoch timestamp to use for filtering activities that have taken place before a certain time. (optional)
after = 56 # Integer | An epoch timestamp to use for filtering activities that have taken place after a certain time. (optional)
page = 56 # Integer | Page number. (optional)
perPage = 56 # Integer | Number of items per page. Defaults to 30. (optional) (default to 30)

# functions

# get athlete activities
def get_activities():
    try: 
        # List Athlete Activities
        api_response = api_instance.getLoggedInAthleteActivities(before=before, after=after, page=page, perPage=perPage)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ActivitiesApi->getLoggedInAthleteActivities: %s\n" % e)

# get activity details
id = 789 # Long | The identifier of the activity.
includeAllEfforts = true # Boolean | To include all segments efforts. (optional)

def get_activity():
    try: 
        # Get Activity
        api_response = api_instance.getActivityById(id,
                                                includeAllEfforts=includeAllEfforts)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ActivitiesApi->getActivityById: %s\n" % e)


# a different approach
from stravalib.client import Client

client = Client()
authorize_url = client.authorization_url(
    client_id=10185,
    redirect_uri='http://127.0.0.1:8001/authorized')
authorize_url
# Have the user click the authorization URL, a 'code' param will be added to the redirect_uri
# .....

# Extract the code from your webapp response
code = request.get('code') # or whatever your framework does
access_token = client.exchange_code_for_token(client_id=1234, client_secret='asdf1234', code=code)

# Now store that access token somewhere (a database?)
client.access_token = access_token
athlete = client.get_athlete()
print("For {id}, I now have an access token {token}".format(id=athlete.id, token=access_token))
