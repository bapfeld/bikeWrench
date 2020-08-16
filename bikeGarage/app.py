import os
import sqlite3
import datetime
import dateparser
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template
# from wtforms import (Form, TextField, TextAreaField,
#                      validators, StringField, SubmitField)
# from bikeGarage import database, strava_funcs, startup_funcs

###########################################################################
# Initial Setup                                                           #
###########################################################################
app = Flask(__name__)
load_dotenv(find_dotenv())
db_path = os.environ.get('STRAVA_DB_PATH')
bdr = os.environ.get('BDR')
schema_path = os.environ.get('SCHEMA_PATH')


###########################################################################
# Flask definition                                                        #
###########################################################################
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


###########################################################################
# Run the app                                                             #
###########################################################################
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
