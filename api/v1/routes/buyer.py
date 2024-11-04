from . import buyer_route
from flask import jsonify, request, make_response
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity
from random import randint
from datetime import datetime
from bson.objectid import ObjectId
from ..models import db, user_collection, deleted_user_collection
from ..models.user import Manager, User, Buyer
import bcrypt
from ..views import permission_required
from ..views.permission import permissions, get_or_create_role
from ..views.verify_accout import send_ver_code


@buyer_route.route('/buyer', strict_slashes=False, methods=['POST'])
def register_buyer():
  """
  Register a new buyer
  ---
  tags:
      - Buyer
  summary: Register a new buyer
  description: Register a new buyer in the system
  parameters:
      - in: body
        name: buyer
        description: The buyer registration information
        required: true
        schema:
          type: object
          required:
            - fullName
            - email
            - phone
            - password
          properties:
            fullName:
              type: string
              description: The first name of the buyer
            email:
              type: string
              format: email
              description: The email address of the buyer
            phone:
              type: string
              description: The phone number of the buyer
            password:
              type: string
              format: password
              description: The password for the buyer's account
  responses:
      201:
          description: buyer registered successfully
          schema:
              type: object
              properties:
                  message:
                      type: string
                      description: Success message
          examples:
              application/json:
                  {
                      "message": "Buyer registered successfully",
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
                      "error": "Record already found, new Email or Phone Number required to proceed",
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

    buyer = Buyer()

    full_name = data.get('fullName')
    email = data.get('email')
    phone_number = data.get('phone')

    buyer.validate_data(data)
    # Extract data
    if email:
      duplicate_email = User.query.filter_by(email=email).first()
      if duplicate_email:
        return jsonify({'error': 'Email already exists'}), 409

    # Check for duplicate buyer in MongoDB
    existing_user = user_collection.find_one({'fullName': full_name})
    if existing_user:
      return jsonify({
      'error': 'Record already found,gkhfl new Email or Phone Number required to proceed',
      'code': 'usr409'
    }), 409

    # Assign values to buyer object
    # buyer.fullName = generate_buyer_fullName()

    role = get_or_create_role("buyer", permissions["buyer"], buyer, 'buyer')
    buyer.phone_number = phone_number
    buyer.roles.append(role)

    # Add and commit to the database
    db.session.add(buyer)
    db.session.commit()

    # Insert the buyer data in MongoDB
    user_collection.insert_one({
    'id': buyer.id,
    'fullName': full_name,
    'email': email,
    'phone_number': phone_number,
    'type': 'buyer',
    'permissions': [perm.code for perm in role.permissions]
    })

    # Create access token

    response = jsonify({
      'message': 'Buyer registered successfully',
      'user': {
        'id': buyer.id,
        'full_name': full_name,
        'email': buyer.email,
        'phone_number': buyer.phone_number,
        'user_type': 'buyer',
      },
      'permissions': [perm.code for perm in role.permissions],
      'roles': [{'id': r.id, 'name': r.name} for r in buyer.roles],
      'last_login': datetime.utcnow().isoformat()
    })

    access_token = create_access_token(identity=buyer.id)
    set_access_cookies(response, access_token)
    send_ver_code(buyer.email)

    return response, 201
  
  except BadRequest as e:
    return jsonify({'error': str(e)}), 400
  except IntegrityError as e:
    db.session.rollback()
    print(e)
    return jsonify({'error': 'Integrity Error Occured'}), 409
  except Exception as e:
    db.session.rollback()
    print(e)
    return jsonify({'error': 'An unexpected error occurred'}), 500


@buyer_route.route('/update_buyer', strict_slashes=False, methods=['PUT'])
def update_buyer():
    """
    Update buyer details
    ---
    tags:
      - Buyer
    summary: Update buyer details
    description: Update buyer details in the system
    parameters:
      - in: body
        name: buyer
        description: The buyer details to be updated
        required: true
        schema:
          type: object
          required:
            - id
          properties:
            id:
              type: string
              description: The ID of the buyer
            full_name:
              type: string
              description: The first name of the buyer
            email:
              type: string
              format: email
              description: The email address of the buyer
            phone_number:
              type: string
              description: The phone number of the buyer
    responses:
      200:
        description: buyer updated successfully
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
    try:
      data = request.get_json()
      if not data or 'id' not in data:
        raise BadRequest('No id provided')

      id = data.get('id')

      # Try to find buyer in MongoDB first
      mongo_buyer = user_collection.find_one({
        '$or': [
          {'id': id},
          {'email': id},
        ]
      })

      if mongo_buyer:
        field_map = {
          'full_name': 'fullName',
          'email': 'email',
          'phone_number': 'phone_number'
        }

        buyer_id = mongo_buyer.get('_id')
        for key, value in field_map.items():
          if key in data:
            user_collection.update_one(
              {'_id': buyer_id},
              {'$set': {value: data[key]}}
            )

      # Also check SQL database
      buyer = Buyer.query.filter(
        (Buyer.id == id) |
        (Buyer.email == id)
      ).first()
      if not buyer:
        return jsonify({'error': 'buyer not found'}), 404
      buyer_id = buyer.id
        
      # Get the specific buyer type instance
      buyer = Buyer.query.get(buyer_id)
      if not buyer:
        return jsonify({'error': 'buyer not found'}), 404

      if 'email' in data and Buyer.query.filter(Buyer.email == data['email'], Buyer.id != buyer.id).first():
        raise BadRequest('Email is already in use')
      
      # Update buyer details in SQL database
      for key in ['full_name', 'email', 'phone_number']:
        if key in data:
          setattr(buyer, key, data[key])

      db.session.commit()

      return jsonify({'message': 'Buyer updated successfully'}), 200

    except BadRequest as e:
      return jsonify({'error': str(e)}), 400
    except IntegrityError:
      db.session.rollback()
      return jsonify({'error': 'Error updating buyer due to integrity constraint', 'code': 'usr409'}), 409
    except Exception as e:
      db.session.rollback()
      print(f"Unexpected error: {str(e)}")
      return jsonify({'error': 'An unexpected error occurred'}), 500
    

@buyer_route.route('/<string:full_name>', strict_slashes=False, methods=['DELETE'])
@jwt_required()
def delete_buyer(full_name):
    """
    Delete buyer
    ---
    tags:
      - Buyer
    parameters:
      - in: path
        name: full_name
        required: true
        schema:
          type: string
          description: buyer Fullname
    responses:
      200:
        description: buyer deleted successfully
        schema:
          full_name: buyer_response
          properties:
            message:
              type: string
              description: Success message
      400:
        description: Bad request
        schema:
          id: error_response
          properties:
            error:
              type: string
              description: Error message
      404:
        description: Record not found
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
      if not full_name:
        raise BadRequest('No Id provided')

      # Try to find buyer in MongoDB first
      mongo_buyer = user_collection.find_one({'fullName': full_name})
      print(mongo_buyer)
      buyer_id = None
      if mongo_buyer:
        buyer_id = mongo_buyer.get('id')
      print(buyer_id)
      if not buyer_id:
        # If not found in MongoDB, check SQL database
        buyer = Buyer.query.filter((Buyer.full_name == full_name)).first()
        if not buyer:
          return jsonify({'error': 'buyer not found'}), 404
        buyer_id = buyer.id

      # Get the specific buyer type instance
      buyer = Buyer.query.get(buyer_id)
      if not buyer:
        return jsonify({'error': 'buyer not found'}), 404

      # Prepare buyer data for archiving
      buyer_dict = {k: v for k, v in buyer.__dict__.items() if not k.startswith('_')}
      buyer_dict['deleted_at'] = datetime.utcnow()

      # Delete from MongoDB and archive
      user_collection.delete_one({'fullName': buyer.full_name})
      deleted_user_collection.insert_one(buyer_dict)

      # Delete from SQL database
      db.session.delete(buyer)
      db.session.commit()

      return jsonify({'message': 'Buyer deleted successfully'}), 200

    except BadRequest as e:
      return jsonify({'error': str(e)}), 400
    except IntegrityError:
      db.session.rollback()
      return jsonify({'error': 'Error deleting buyer due to integrity constraint', 'code': 'usr409'}), 409
    except Exception as e:
      db.session.rollback()
      print(f"Unexpected error: {str(e)}")
      return jsonify({'error': 'An unexpected error occurred'}), 500

