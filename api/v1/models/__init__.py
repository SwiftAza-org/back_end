from ..database.mysql import db
from ..database.mongodb import get_mongo_client
from ..config import config
from os import environ
from uuid import uuid4


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.String(36), primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now()
    )

    def __init__(self):
        self.id = str(uuid4())


mongod_client = get_mongo_client()
default_collection = mongod_client[config[environ.get('FLASK_ENV', 'development')].MONGO_URI.split('/')[-1]]  # noqa: E501
user_collection = default_collection['users']
deleted_user_collection = default_collection['deleted_user']
