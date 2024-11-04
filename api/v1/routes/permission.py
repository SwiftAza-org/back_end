from . import user_permission_route
from flask import jsonify, request
from datetime import datetime
from ..models.user import Manager, Buyer, Seller, User, Role, Permission
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, deleted_user_collection, user_collection


@user_permission_route.route('/user', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_user_permissions_route():
    """
    Retrieve User Permissions

    ---
    tags:
      - Permission
    summary: Get a user's permissions
    description: Retrieve the permission codes and descriptions associated with the current user's role based on the user ID in the JWT.
    responses:
      200:
        description: Permissions retrieved successfully
        schema:
          type: object
          properties:
            permissions:
              type: array
              items:
                type: object
                properties:
                  code:
                    type: string
                    description: Permission code
                  description:
                    type: string
                    description: Description of the permission
        examples:
          application/json:
            {
              "permissions": [
                {
                  "code": "PERM001",
                  "description": "Access to account data"
                },
                {
                  "code": "PERM002",
                  "description": "Manage user accounts"
                }
              ]
            }
      400:
        description: Bad request due to invalid user data
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
        examples:
          application/json:
            {
              "error": "Invalid user data"
            }
      404:
        description: User not found in MongoDB or SQL database
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
        examples:
          application/json:
            {
              "error": "User not found"
            }
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
        examples:
          application/json:
            {
              "error": "An unexpected error occurred"
            }
    """
    try:
        current_user_id = get_jwt_identity()
        # First, try to get the user from MongoDB
        user_mongo = user_collection.find_one({'id': current_user_id})
        data_type = {
            'manager': Manager,
            'proprietor': Buyer,
            'seller': Seller
        }
        if user_mongo:
            user_type = user_mongo.get('type')
            email = user_mongo.get('email')
        else:
            # If not found in MongoDB, try SQL database
            user_sql = User.query.get(current_user_id)
            if not user_sql:
                return jsonify({'error': 'User not found'}), 404
            user_type = next((k for k, v in data_type.items() if isinstance(user_sql, v)), None)
            email = user_sql.email

        if not user_type or not email:
            return jsonify({'error': 'Invalid user data'}), 400

        # Get the user from SQL database based on the email
        user = data_type[user_type].query.filter(
            (data_type[user_type].email == email)
        ).first()

        if not user:
            return jsonify({'error': 'User not found in SQL database'}), 404

        # Collect permissions from all roles
        permissions = set()
        for role in user.roles:
            permissions.update(permission.code for permission in role.permissions)

        return jsonify({'permissions': list(permissions)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500