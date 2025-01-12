from os import environ
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv('.env')

DB_HOST = environ.get('DB_HOST', 'localhost')
MONGODB_PORT = environ.get('MONGODB_PORT', '27017')
MONGODB_HOST = environ.get('MONGODB_HOST', 'localhost')
DB_PORT = environ.get('DB_PORT', '3306')
DB_TYPE = environ.get('DB_TYPE', 'mysql+pymysql')

DB_USERNAME = environ.get('DB_USERNAME', 'swaz_user')
DB_PASSWORD = environ.get('DB_PASSWORD', 'swaz_psswd')
DB_NAME = environ.get('DB_NAME', 'swaz_db')


class Config:
    SECRET_KEY = environ.get('SECRET_KEY', 'hard to guess string')
    JWT_SECRET_KEY = environ.get('JWT_SECRET_KEY', 'hard_to_guess_string')
    JWT_TOKEN_LOCATION = ['headers', 'cookies']

    # Gmail SMTP Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = environ.get('MAIL_USERNAME', 'swaz_email@gmail.com')
    MAIL_PASSWORD = environ.get('MAIL_PASSWORD', 'your_gmail_password')
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER', 'swaz_email@gmail.com')
    TWILIO_ACCOUNT_SID = environ.get('TWILIO_ACCOUNT_SID', 'your_twilio_account_sid')
    TWILIO_AUTH_TOKEN = environ.get('TWILIO_AUTH_TOKEN', 'your_twilio_auth_token')
    TWILIO_PHONE_NUMBER = environ.get('TWILIO_PHONE_NUMBER', 'your_twilio_phone_number')

    SQLALCHEMY_DATABASE_URI = environ.get(
        'DATABASE_URL',
        f'{DB_TYPE}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'  # noqa: E501
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    mongo_uri = f'mongodb://{DB_USERNAME}:{DB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{DB_NAME}'  # noqa: E501
    # mongo_uri = f'mongodb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{MONGODB_PORT}/{DB_NAME}?authSource={DB_NAME}'  # noqa: E501
    MONGO_URI = environ.get('MONGO_URI', mongo_uri)

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    PROPAGATE_EXCEPTIONS = True
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    SWAGGER = {
        'title': 'Daily Contribution API',
        'uiversion': 3,
        'version': '1.0.1',
        'description': 'API documentation for Daily Contribution',
        'termsOfService': '',
        'license': {
            'name': 'MIT',
            'url': 'https://opensource.org/licenses/MIT'
        },
        'schemes': [
            'http',
            'https'
        ],
        'basePath': '/',
    }


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    # PREFERRED_URL_SCHEME = 'https'
    # SESSION_COOKIE_SECURE = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_COOKIE_CSRF_PROTECT = True
    SWAGGER = {
        'title': 'Daily Contribution API',
        'uiversion': 3,
        'version': '1.0.1',
        'description': 'API documentation for Daily Contribution',
        'termsOfService': '',
        'license': {
            'name': 'MIT',
            'url': 'https://opensource.org/licenses/MIT'
        },
        'schemes': [
            'https'
        ],
        'basePath': '/',
    }


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
