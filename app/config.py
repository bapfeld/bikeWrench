import os
from dotenv import load_dotenv
import keyring

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Basic/base configuration"""

    # General Flask
    WTF_CSRF_ENABLED = False
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

    # Database
    DB_PATH = os.environ.get('STRAVA_DB_PATH')
    SCHEMA_PATH = os.environ.get('SCHEMA_PATH')

    # Strava secrets
    CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    APP_CODE = keyring.get_password('bikeWrench', 'code')


class DevConfig(Config):
    """Development configuration"""
    
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True


class ProdConfig(Config):
    """Production configuration"""
    
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
