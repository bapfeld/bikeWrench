import os
# from dotenv import load_dotenv
import keyring

# basedir = os.path.abspath(os.path.dirname(__file__))
# load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Basic/base configuration"""

    # General Flask
    WTF_CSRF_ENABLED = False
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'


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
