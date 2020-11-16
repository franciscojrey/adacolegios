from flask import Flask

app = Flask(__name__)
if app.config["ENV"] == "production":
    app.config.from_object('config.ProductionConfig')
elif app.config["ENV"] == "development":
    app.config.from_object('config.DevelopmentConfig')
else: 
    app.config.from_object('config.TestingConfig')

from adacolegios import auth
from adacolegios import posts
from adacolegios import notas
from adacolegios import cuenta
from adacolegios import main_functions
from adacolegios import perfiles