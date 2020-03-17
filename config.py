import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            "postgresql://postgres:public@localhost:25432/ictes"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_KEY = 'ictes710-MbedDisco'
    MODEL_FILE = 'model.h5'
    MQTT_BROKER_URL = 'mqtt.netpie.io'
    MQTT_BROKER_PORT = 1883
    MQTT_CLIENT_ID = '5769c42c-f897-47a0-9787-c59059a9429e'
    MQTT_TOKEN = 'Qt46TTPzHu47krUc6FNZdLiXYLpqJgu5'
