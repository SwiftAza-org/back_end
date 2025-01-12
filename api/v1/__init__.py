from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail
from .config import config
from .database.mysql import db
from .database.mongodb import init_mongodb, mongo  # noqa: F401

from .routes import auth_route, root_route, user_route# noqa: F401


bcrypt = Bcrypt()
cors = CORS(supports_credentials=True)


def create_app(config_name: str) -> Flask:
    print(f"Creating app with config: {config_name}")
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    Swagger(app)
    bcrypt.init_app(app)
    JWTManager(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    db.init_app(app)
    init_mongodb(app)
    Migrate(app, db)
    Mail(app)

    # Register blueprints here
    app.register_blueprint(root_route)
    app.register_blueprint(auth_route)
    app.register_blueprint(user_route)

    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    @app.route('/')
    def home():
        return jsonify({"message": "Welcome to Daily Contribution API"})

    with app.app_context():
        db.create_all()

    return app
