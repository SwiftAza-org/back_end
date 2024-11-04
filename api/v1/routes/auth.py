from . import auth_route
from flask import jsonify, request, make_response
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies, set_access_cookies
from random import randint
from datetime import datetime
from bson.objectid import ObjectId

from ..models import user_collection, db
from ..views.permission import data_type
from ..models.user import Manager, User, Seller, Buyer
from ..views.util import to_dict
import bcrypt
from ..views.verify_accout import send_ver_code, cleanup_expired_codes, is_verification_code_valid



@auth_route.route('/login', strict_slashes=False, methods=['POST'])
def login():
    """
    Login a user
    ---
    tags:
        - Auth
    parameters:
        - in: body
          name: body
          required: true
          schema:
            id: login_request
            properties:
                email:
                    type: string
                    description: email of the user
                password:
                    type: string
                    description: User password
    responses:
        200:
            description: User logged in successfully
            schema:
                id: login_response
                properties:
                    message:
                        type: string
                        description: Success message
                    user_type:
                        type: string
                        description: User type
                    last_login:
                        type: string
                        description: Last login date
        400:
            description: Bad request
            schema:
                id: error_response
                properties:
                    error:
                        type: string
                        description: Error message
        401:
            description: Unauthorized
            schema:
                id: error_response
                properties:
                    error:
                        type: string
                        description: Error message
        500:
            description: Internal Server Error
            schema:
                id: error_response
                properties:
                    error:
                        type: string
                        description: Error message
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'error': 'Bad request: Missing credentials'}), 400

        # Query MongoDB
        mongodata = user_collection.find_one({'email': email})
        if not mongodata:
            return jsonify({'error': 'User not found'}), 401

        user_type = mongodata.get('type', '').lower()
        if user_type not in data_type:
            return jsonify({'error': 'Invalid user type'}), 500

        # Query MySQL
        try:
            user = data_type[user_type].query.filter_by(email=mongodata['email']).one()
        except NoResultFound:
            return jsonify({'error': 'User not found in MySQL database'}), 401

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({'error': 'Invalid password'}), 401

        # Update MongoDB
        now = datetime.utcnow()
        user_collection.update_one(
            {'_id': mongodata['_id']},
            {
                '$set': {
                    'last_login': now,
                    'id': user.id
                }
            }
        )

        # Fetch additional data
        roles = user.roles
        permissions = set()
        for role in roles:
            permissions.update([perm.code for perm in role.permissions])

        # Create access token
        access_token = create_access_token(identity=user.id)

        # Prepare response data
        response_data = {
            'message': 'Login Successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'user_type': user_type,
                'phone_number': user.phone_number if hasattr(user, 'phone_number') else None,
            },
            'permissions': list(permissions),
            'roles': [{'id': role.id, 'name': role.name} for role in roles],
            'last_login': now.isoformat(),
            'token': access_token
        }

        # Prepare response
        response = make_response(jsonify(response_data))
        
        # Set access token cookie
        set_access_cookies(response, access_token)
        response.headers['Authorization'] = f'Bearer {access_token}'
        
        return response, 200

    except Exception as e:
        print(f"Error in login: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An unexpected error occurred. Please try again later. {str(e)} '}), 500


@auth_route.route('/verify_user', strict_slashes=False, methods=['POST'])
def verify_account():
    """
    Verify user account
    ---
    tags:
      - Auth
    summary: Verify user account
    description: Verify user account in the system
    parameters:
      - in: body
        name: buyer
        description: The buyer details to be verified
        required: true
        schema:
          type: object
          required:
            - email
            - code
          properties:
            email:
              type: string
              format: email
              description: The email address of the buyer
            code:
              type: string
              description: The verification code
    responses:
      200:
        description: Account verified successfully
        schema:
          type: object
          properties:
            message:
              type: string
              description: Success message
      400:
        description: Bad request
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
      404:
        description: Record not found
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
      500:
        description: Internal Server Error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
    """
    cleanup_expired_codes()
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        raise BadRequest('Bad Request: Missing email or code')

    is_valid = is_verification_code_valid(email, code)
    if not is_valid:
        return jsonify({'error': 'Code Expired'}), 401

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.validated = True

    user_collection.update_one({'validated': True}, {'$set': user})
    db.session.commit()
    return jsonify({'message': 'Account verified successfully'}), 200


@auth_route.route('/logout', strict_slashes=False, methods=['POST'])
@jwt_required()
def logout():
    """
    Logout a user
    ---
    tags:
        - Auth
    responses:
        200:
            description: User logged out successfully
            schema:
                id: logout_response
                properties:
                    message:
                        type: string
                        description: Success message
        500:
            description: Internal Server Error
            schema:
                id: error_response
                properties:
                    error:
                        type: string
                        description: Error message
    """
    try:
        # Get the user's identity
        mysql_user_id = get_jwt_identity()

        if mysql_user_id is None:
            return jsonify({'error': 'User is not logged in'}), 401

        # Find the user in MongoDB using the MySQL user ID
        mongodata = user_collection.find_one({'id': mysql_user_id})

        if not mongodata:
            user = User.query.get(mysql_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            mongodata = user_collection.find_one({'fullname': user.fullname})
            if not mongodata:
                return jsonify({'error': 'User not found in MongoDB'}), 404


        # Update last logout in MongoDB
        user_collection.update_one(
            {'_id': mongodata['_id']},
            {'$set': {'last_logout': datetime.utcnow()}}
        )

        # Clear the JWT cookies
        response = make_response(jsonify({"message": "Successfully logged out"}))
        unset_jwt_cookies(response)

        return response, 200

    except Exception:
        return jsonify({'error': 'An unexpected error occurred'}), 500


@auth_route.route('/status', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_status():
    """
    Get user status
    ---
    tags:
        - Auth
    responses:
        200:
            description: User status retrieved successfully
            schema:
                id: status_response
                properties:
                    message:
                        type: string
                        description: Success message
                    user_type:
                        type: string
                        description: User type
                    last_login:
                        type: string
                        description: Last login date
        500:
            description: Internal Server Error
            schema:
                id: error_response
                properties:
                    error:
                        type: string
                        description: Error message
    """
    try:
        mysql_user_id = get_jwt_identity()
        
        if mysql_user_id is None:
            return jsonify({'error': 'User is not logged in'}), 401

        user = User.query.get(mysql_user_id)
        Owner = data_type[user.type].query.get(mysql_user_id)
        roles = Owner.roles
        permissions = []
        for role in roles:
            if role:
                permissions.extend(perm.code for perm in role.permissions)
        
        mongodata = user_collection.find_one({
            '$or': [
                {'email': user.email},
                {'id': user.id}
            ]
        })

        if not mongodata:
            return jsonify({'error': 'User not found in MongoDB'}), 404

        return jsonify({
            'message': 'User status retrieved successfully',
            'isAuthenticated': True,
            'user_type': mongodata['type'],
            'last_login': mongodata.get('last_login', None),
            'user': {
                'id': Owner.id,
                'full_name': Owner.full_name,
                'email': Owner.email,
                'phone_number': Owner.phone_number if hasattr(Owner, 'phone_number') else None,
                'user_type': Owner.type,
            },
            'permissions': permissions,
            'roles': [{'id': role.id, 'name': role.name} for role in roles],
            'last_login': datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        print(f"Error in get_status: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
