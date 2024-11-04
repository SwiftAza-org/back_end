from .mysql import db as mysql_db, init_mysql, get_mysql_session, init_mysql_db
from .mongodb import mongo, init_mongodb, get_mongo_client


class DatabaseManager:
    def __init__(self):
        self.mysql_db = mysql_db
        self.mongo = mongo

    def init_app(self, app):
        init_mysql(app)
        init_mongodb(app)

    def get_mysql_session(self):
        return get_mysql_session()

    def get_mongo_client(self):
        return get_mongo_client()

    def init_mysql_db(self, app):
        init_mysql_db(app)


db_manager = DatabaseManager()
