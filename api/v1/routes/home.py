from . import root_route
from flask import jsonify, request
from datetime import datetime
from ..models.user import User
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest
from flask_jwt_extended import jwt_required
from ..models import db, deleted_user_collection, user_collection


@root_route.route('/', strict_slashes=False)
def index():
    """
    This is the root route
    ---
    responses:
        200:
            description: A simple message
            content:
            application/json:
                schema:
                type: object
                properties:
                    status:
                    type: string
    """
    return jsonify({'status': 'ok'})

@root_route.route('/users', strict_slashes=False)
def all_user():
    """
    This is the root route
    ---
    responses:
        200:
            description: A simple message
            content:
            application/json:
                schema:
                type: object
                properties:
                    status:
                    type: string
    """
    users = User.query.all()
    mongo_users = user_collection.find()
    return jsonify(
        {
            'users': [
                {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role.name,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                } for user in users
            ],
            'mongo_users': [
                {
                    'id': user.get("id"),
                    'email': user.get("email"),
                    'role': user.get("role"),
                    'created_at': user.get("created_at"),
                    'updated_at': user.get("updated_at")
                } for user in mongo_users
            ]
        }
    )