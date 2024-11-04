from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from os import environ

from ..config import config

db = SQLAlchemy()


def init_mysql(app):
    db.init_app(app)


def get_mysql_session():
    engine = create_engine(
        config[environ.get('FLASK_ENV', 'development')].SQLALCHEMY_DATABASE_URI
    )
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base = declarative_base()
    Base.query = db_session.query_property()
    return db_session


def init_mysql_db(app):
    with app.app_context():
        db.create_all()
