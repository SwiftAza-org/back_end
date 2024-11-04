from flask_pymongo import PyMongo
from pymongo import MongoClient
from os import environ

from ..config import config

mongo = PyMongo()


def init_mongodb(app):
    mongo.init_app(app)


def get_mongo_client():
    return MongoClient(
        config[environ.get('FLASK_ENV', 'development')].MONGO_URI
    )
