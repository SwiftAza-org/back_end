from . import user_route
from flask import jsonify, request, make_response
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity
from random import randint
from datetime import datetime
from bson.objectid import ObjectId
from ..models import db, user_collection, deleted_user_collection
from ..models.user import  User, Wallet
import bcrypt
from ..views.verify_accout import send_ver_code
import traceback


@user_route.route('/user', strict_slashes=False, methods=['POST'])
def register_user():
  """
  Register a new user
  ---
  tags:
      - User
  summary: Register a new user
  description: Register a new user in the system
  parameters:
      - in: body
        name: user
        description: The user registration information
        required: true
        schema:
          type: object
          required:
            - fullName
            - card_number
            - phone_number
            - account_type
          properties:
            fullName:
              type: string
              description: The full name of the user
            card_number:
              type: string
              format: card_number
              description: The card number of the user
            phone_number:
              type: string
              description: The phone number of the user
            account_type:
              type: string
              format: account_type
              description: The account_type for the user's account
  responses:
      201:
          description: User registered successfully
          schema:
              type: object
              properties:
                  message:
                      type: string
                      description: Success message
                  user:
                      type: object
                      properties:
                          id:
                              type: string
                              description: The ID of the user
                          fullName:
                              type: string
                              description: The full name of the user
                          card_number:
                              type: string
                              description: The card number of the user
                          phone_number:
                              type: string
                              description: The phone number of the user
                          account_type:
                              type: string
                              description: The account type of the user
          examples:
              application/json:
                  {
                      "message": "User registered successfully",
                      "user": {
                          "id": "12345",
                          "fullName": "John Doe",
                          "card_number": "1234-5678-9012-3456",
                          "phone_number": "123-456-7890",
                          "account_type": "standard"
                      }
                  }
      400:
          description: Bad request due to missing or invalid input
          schema:
              type: object
              properties:
                  error:
                      type: string
                      description: Error message
          examples:
              application/json:
                  {
                      "error": "No input data provided"
                  }
      409:
          description: Conflict due to existing record
          schema:
              type: object
              properties:
                  error:
                      type: string
                      description: Conflict message
                  code:
                      type: string
                      description: Error code indicating the type of conflict
          examples:
              application/json:
                  {
                      "error": "Record already found, new card_number or Phone Number required to proceed",
                      "code": "usr409"
                  }
      500:
          description: Unexpected internal server error
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
    data = request.get_json()
    if not data:
      raise BadRequest("No input data provided")

    user = User()
    wallet = Wallet(user_id=user.id)

    full_name = data.get('fullName')
    card_number = data.get('card_number')
    phone_number = data.get('phone_number')
    account_type = data.get('account_type')


    user.validate_data(data)
    # Extract data
    if card_number:
      duplicate_card_number = User.query.filter_by(card_number=card_number).first()
      if duplicate_card_number:
        return jsonify({'error': 'Card number already exists'}), 409

    # Check for duplicate user in MongoDB
    existing_user = user_collection.find_one({'card_number': card_number})
    if existing_user:
      return jsonify({
      'error': 'Record already found, new card number or Phone Number required to proceed',
      'code': 'usr409'
    }), 409

    # Assign values to user object
    # user.fullName = generate_user_fullName()

    user.full_name = full_name
    user.phone_number = phone_number
    user.card_number = card_number
    user.account_type = [account_type] if not isinstance(account_type, list) else account_type
    user.balance = wallet.balance
    wallet.card_number = card_number
    wallet.user_id = user.id

    # Add and commit to the database
    db.session.add(user)
    db.session.commit()

    # Insert the user data in MongoDB
    user_collection.insert_one({
    'id': user.id,
    'fullName': full_name,
    'card_number': card_number,
    'phone_number': phone_number,
    'account_type': 'account_type',
    })

    # Create access token

    response = jsonify({
      'message': 'User registered successfully',
      'user': {
        'id': user.id,
        'fullName': full_name,
        'card_number': card_number,
        'phone_number': phone_number,
        'account_type': 'account_type',
      },
    })

    return response, 201
  
  except BadRequest as e:
    return jsonify({'error': str(e)}), 400
  except IntegrityError as e:
    db.session.rollback()
    print(e)
    return jsonify({'error': 'Integrity Error Occured'}), 409
  except Exception as e:
    db.session.rollback()
    print(traceback.format_exc())
    return jsonify({'error': 'An unexpected error occurred'}), 500

@user_route.route('/get_all_users', strict_slashes=False, methods=['GET'])
def get_all_users():
  """
  Get all users
  ---
  tags:
    - User
  summary: Get all users
  description: Get all users in the system
  responses:
    200:
      description: Users retrieved successfully
      schema:
        type: object
        properties:
          users:
            type: array
            items:
              type: object
              properties:
                id:
                  type: string
                  description: The ID of the user
                fullName:
                  type: string
                  description: The full name of the user
                card_number:
                  type: string
                  description: The card number of the user
                phone_number:
                  type: string
                  description: The phone number of the user
                account_type:
                  type: string
                  description: The account type of the user
      examples:
        application/json:
          {
            "users": [
              {
                "id": "12345",
                "fullName": "John Doe",
                "card_number": "1234-5678-9012-3456",
                "phone_number": "123-456-7890",
                "account_type": "standard"
              }
            ]
          }
    404:
      description: Record not found
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message
      examples:
        application/json:
          {
            "error": "No users found"
          }
    500:
      description: Unexpected internal server error
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
    users = User.query.all()
    if not users:
      return jsonify({'error': 'No users found'}), 404

    users = [
      {
        'id': user.id,
        'fullName': user.full_name,
        'card_number': user.card_number,
        'phone_number': user.phone_number,
        'account_type': user.account_type,
      }
      for user in users
    ]

    return jsonify({'users': users}), 200
  except Exception as e:
    print(f"Unexpected error: {str(e)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500
  
@user_route.route('/get_user/<string:card_number>', strict_slashes=False, methods=['GET'])
def get_user(card_number):
  """
  Get user
  ---
  tags:
    - User
  summary: Get a user
  description: Get a user from the system
  parameters:
    - in: path
      name: card_number
      required: true
      schema:
        type: string
        description: The card number of the user
  responses:
    200:
      description: User retrieved successfully
      schema:
        type: object
        properties:
          id:
            type: string
            description: The ID of the user
          fullName:
            type: string
            description: The full name of the user
          card_number:
            type: string
            description: The card number of the user
          phone_number:
            type: string
            description: The phone number of the user
          account_type:
            type: string
            description: The account type of the user
      examples:
        application/json:
          {
            "id": "12345",
            "fullName": "John Doe",
            "card_number": "1234-5678-9012-3456",
            "phone_number": "123-456-7890",
            "account_type": "standard"
          }
    404:
      description: Record not found
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
      description: Unexpected internal server error
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
    user = User.query.filter_by(card_number=card_number).first()
    if not user:
      return jsonify({'error': 'User not found'}), 404

    user = {
      'id': user.id,
      'full_name': user.full_name,
      'card_number': user.card_number,
      'phone_number': user.phone_number,
      'account_type': user.account_type,
      'balance': user.balance,
    }

    return jsonify(user), 200
  except Exception as e:
    print(f"Unexpected error: {str(e)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

@user_route.route('/update_user', strict_slashes=False, methods=['PUT'])
def update_user():
  """
  Update user details
  ---
  tags:
    - User
  summary: Update user details
  description: Update user details in the system
  parameters:
    - in: body
      name: user
      description: The user details to be updated
      required: true
      schema:
        type: object
        required:
          - id
        properties:
          id:
            type: string
            description: The ID of the user
          fullName:
            type: string
            description: The full name of the user
          card_number:
            type: string
            format: card_number
            description: The card number of the user
          phone:
            type: string
            description: The phone number of the user
  responses:
    200:
      description: User updated successfully
      schema:
        type: object
        properties:
          message:
            type: string
            description: Success message
      examples:
        application/json:
          {
            "message": "User updated successfully"
          }
    400:
      description: Bad request due to missing or invalid input
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message
      examples:
        application/json:
          {
            "error": "No id provided"
          }
    404:
      description: Record not found
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
      description: Unexpected internal server error
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
    data = request.get_json()
    if not data or 'id' not in data:
      raise BadRequest('No id provided')

    id = data.get('id')

    # Try to find user in MongoDB first
    mongo_user = user_collection.find_one({
    '$or': [
      {'id': id},
      {'card_number': id},
    ]
    })

    if mongo_user:
      field_map = {
        'fullName': 'fullName',
        'card_number': 'card_number',
        'phone': 'phone_number'
      }

    user_id = mongo_user.get('_id')
    for key, value in field_map.items():
      if key in data:
        user_collection.update_one(
          {'_id': user_id},
          {'$set': {value: data[key]}}
        )

    # Also check SQL database
    user = User.query.filter(
      (User.id == id) |
      (User.card_number == id)
      ).first()
    
    if not user:
      return jsonify({'error': 'user not found'}), 404
    user_id = user.id
    
    # Get the specific user type instance
    user = User.query.get(user_id)
    if not user:
      return jsonify({'error': 'user not found'}), 404

    if 'card_number' in data and User.query.filter(User.card_number == data['card_number'], User.id != user.id).first():
      raise BadRequest('card_number is already in use')
    
    # Update user details in SQL database
    for key in ['fullName', 'card_number', 'phone']:
      if key in data:
        setattr(user, key, data[key])

    db.session.commit()

    return jsonify({'message': 'user updated successfully'}), 200

  except BadRequest as e:
    return jsonify({'error': str(e)}), 400
  except IntegrityError:
    db.session.rollback()
    return jsonify({'error': 'Error updating user due to integrity constraint', 'code': 'usr409'}), 409
  except Exception as e:
    db.session.rollback()
    print(f"Unexpected error: {str(e)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500
  

@user_route.route('/<string:card_number>', strict_slashes=False, methods=['DELETE'])
def delete_user(card_number):
  """
  Delete user
  ---
  tags:
    - User
  summary: Delete a user
  description: Delete a user from the system
  parameters:
    - in: path
      name: card_number
      required: true
      schema:
        type: string
        description: The card number of the user
  responses:
    200:
      description: User deleted successfully
      schema:
        type: object
        properties:
          message:
            type: string
            description: Success message
      examples:
        application/json:
          {
            "message": "User deleted successfully"
          }
    400:
      description: Bad request due to missing or invalid input
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message
      examples:
        application/json:
          {
            "error": "No Id provided"
          }
    404:
      description: Record not found
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
      description: Unexpected internal server error
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
    if not card_number:
      raise BadRequest('No Id provided')

    # Try to find user in MongoDB first
    mongo_user = user_collection.find_one({'card_number': card_number})
    user_id = None
    if mongo_user:
      user_id = mongo_user.get('id')
    if not user_id:
      # If not found in MongoDB, check SQL database
      user = User.query.filter((User.card_number == card_number)).first()
    if not user:
      return jsonify({'error': 'user not found'}), 404
    user_id = user.id

    # Get the specific user type instance
    user = User.query.get(user_id)
    if not user:
      return jsonify({'error': 'user not found'}), 404

    # Prepare user data for archiving
    user_dict = {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
    user_dict['deleted_at'] = datetime.utcnow()

    # Delete from MongoDB and archive
    user_collection.delete_one({'card_number': user.card_number})
    deleted_user_collection.insert_one(user_dict)

    # Delete from SQL database
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'user deleted successfully'}), 200

  except BadRequest as e:
    return jsonify({'error': str(e)}), 400
  except IntegrityError:
    db.session.rollback()
    return jsonify({'error': 'Error deleting user due to integrity constraint', 'code': 'usr409'}), 409
  except Exception as e:
    db.session.rollback()
    print(f"Unexpected error: {str(e)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500
