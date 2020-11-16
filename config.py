import os

class Config(object):
    DEBUG = False
    TESTING = False

    SECRET_KEY = os.environ["SECRET_KEY"]
    SESSION_COOKIE_SECURE = True

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

    DB_NAME = os.environ["DB_NAME"]
    DB_USERNAME = os.environ["DB_USERNAME"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_SERVER = os.environ["DB_SERVER"]

    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    TESTING = True
    
    SESSION_COOKIE_SECURE = False
