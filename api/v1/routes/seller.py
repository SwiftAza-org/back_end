from . import seller_route
from flask import jsonify, request, make_response
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity
from random import randint
from datetime import datetime
from bson.objectid import ObjectId
from ..models import db, user_collection, deleted_user_collection
from ..models.user import Manager, Seller, User
import bcrypt
from ..views import permission_required
from ..views.permission import permissions, get_or_create_role
from ..views.verify_accout import send_ver_code


@seller_route.route('/seller', strict_slashes=False, methods=['POST'])
def register_seller():
  """
  Register a new seller
  ---
  tags:
      - Seller
  summary: Register a new seller
  description: Register a new seller in the system
  parameters:
      - in: body
        name: seller
        description: The seller registration information
        required: true
        schema:
          type: object
          required:
            - fullName
            - email
            - phone_number
            - password
          properties:
            fullName:
              type: string
              description: The first name of the seller
            email:
              type: string
              format: email
              description: The email address of the seller
            phone_number:
              type: string
              description: The phone number of the seller
            password:
              type: string
              format: password
              description: The password for the seller's account
  responses:
      201:
          description: seller registered successfully
          schema:
              type: object
              properties:
                  message:
                      type: string
                      description: Success message
          examples:
              application/json:
                  {
                      "message": "seller registered successfully",
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

    seller = Seller()

    full_name = data.get('fullName')
    email = data.get('email')

    seller.validate_data(data)
    # Extract data
    if email:
      duplicate_email = User.query.filter_by(email=email).first()
      if duplicate_email:
        return jsonify({'error': 'Email already exists'}), 409
      
    phone_number = data.get('phone') or data.get('phone_number')

    # Check for duplicate seller in MongoDB
    existing_user = user_collection.find_one({'fullName': full_name})
    if existing_user:
      return jsonify({
      'error': 'Record already found, new Email or Phone Number required to proceed',
      'code': 'usr409'
    }), 409

    # Assign values to seller object
    # seller.fullName = generate_seller_fullName()

    role = get_or_create_role("seller", permissions["seller"], seller, 'seller')
    seller.phone_number = phone_number
    seller.roles.append(role)

    # Add and commit to the database
    db.session.add(seller)
    db.session.commit()

    # Insert the seller data in MongoDB
    user_collection.insert_one({
    'id': seller.id,
    'fullName': full_name,
    'email': email,
    'phone_number': phone_number,
    'type': 'seller',
    'permissions': [perm.code for perm in role.permissions]
    })


    # Create access token

    response = jsonify({
      'message': 'Seller registered successfully',
      'user': {
        'id': seller.id,
        'full_name': full_name,
        'email': seller.email,
        'phone_number': seller.phone_number,
        'user_type': 'seller',
      },
      'permissions': [perm.code for perm in role.permissions],
      'roles': [{'id': r.id, 'name': r.name} for r in seller.roles],
      'last_login': datetime.utcnow().isoformat()
    })

    access_token = create_access_token(identity=seller.id)
    set_access_cookies(response, access_token)
    send_ver_code(seller.email)

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

 
@seller_route.route('/update_seller', strict_slashes=False, methods=['PUT'])
def update_seller():
    """
    Update seller details
    ---
    tags:
      - Seller
    summary: Update seller details
    description: Update seller details in the system
    parameters:
      - in: body
        name: seller
        description: The seller details to be updated
        required: true
        schema:
          type: object
          required:
            - id
          properties:
            id:
              type: string
              description: The ID of the seller
            full_name:
              type: string
              description: The full name of the seller
            email:
              type: string
              format: email
              description: The email address of the seller
            phone_number:
              type: string
              description: The phone number of the seller
    responses:
      200:
        description: seller updated successfully
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

      # Try to find seller in MongoDB first
      mongo_seller = user_collection.find_one({
        '$or': [
          {'id': id},
          {'email': id},
        ]
      })

      if mongo_seller:
        field_map = {
          'full_name': 'fullName',
          'email': 'email',
          'phone_number': 'phone_number'
        }

        seller_id = mongo_seller.get('_id')
        for key, value in field_map.items():
          if key in data:
            user_collection.update_one(
              {'_id': seller_id},
              {'$set': {value: data[key]}}
            )
        
      print(id)
      # Also check SQL database
      seller = Seller.query.filter(
        (Seller.id == id) |
        (Seller.email == id)
      ).first()
      print(seller)
      if not seller:
        return jsonify({'error': 'Seller not found'}), 404
      seller_id = seller.id
        
      # Get the specific seller type instance
      seller = Seller.query.get(seller_id)
      if not seller:
        return jsonify({'error': 'seller not found'}), 404

      if 'email' in data and Seller.query.filter(Seller.email == data['email'], Seller.id != seller.id).first():
        raise BadRequest('Email is already in use')
      
      # Update seller details in SQL database
      for key in ['full_name', 'email', 'phone_number']:
        if key in data:
          setattr(seller, key, data[key])

      db.session.commit()

      return jsonify({'message': 'Seller updated successfully'}), 200

    except BadRequest as e:
      return jsonify({'error': str(e)}), 400
    except IntegrityError:
      db.session.rollback()
      return jsonify({'error': 'Error updating seller due to integrity constraint', 'code': 'usr409'}), 409
    except Exception as e:
      db.session.rollback()
      print(f"Unexpected error: {str(e)}")
      return jsonify({'error': 'An unexpected error occurred'}), 500
    

@seller_route.route('/<string:full_name>', strict_slashes=False, methods=['DELETE'])
@jwt_required()
def delete_seller(full_name):
    """
    Delete seller
    ---
    tags:
      - Seller
    parameters:
      - in: path
        name: full_name
        required: true
        schema:
          type: string
          description: seller Fullname
    responses:
      200:
        description: seller deleted successfully
        schema:
          full_name: seller_response
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

      # Try to find seller in MongoDB first
      mongo_seller = user_collection.find_one({'fullName': full_name})
      print(mongo_seller)
      seller_id = None
      if mongo_seller:
        seller_id = mongo_seller.get('id')
      print(seller_id)
      if not seller_id:
        # If not found in MongoDB, check SQL database
        seller = Seller.query.filter((Seller.full_name == full_name)).first()
        if not seller:
          return jsonify({'error': 'Seller not found'}), 404
        seller_id = seller.id

      # Get the specific seller type instance
      seller = Seller.query.get(seller_id)
      if not seller:
        return jsonify({'error': 'seller not found'}), 404

      # Prepare seller data for archiving
      seller_dict = {k: v for k, v in seller.__dict__.items() if not k.startswith('_')}
      seller_dict['deleted_at'] = datetime.utcnow()

      # Delete from MongoDB and archive
      user_collection.delete_one({'fullName': seller.full_name})
      deleted_user_collection.insert_one(seller_dict)

      # Delete from SQL database
      db.session.delete(seller)
      db.session.commit()

      return jsonify({'message': 'Seller deleted successfully'}), 200

    except BadRequest as e:
      return jsonify({'error': str(e)}), 400
    except IntegrityError:
      db.session.rollback()
      return jsonify({'error': 'Error deleting seller due to integrity constraint', 'code': 'usr409'}), 409
    except Exception as e:
      db.session.rollback()
      print(f"Unexpected error: {str(e)}")
      return jsonify({'error': 'An unexpected error occurred'}), 500

