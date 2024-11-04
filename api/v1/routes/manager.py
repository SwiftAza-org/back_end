from . import manager_route
from flask import jsonify, request, make_response
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, verify_jwt_in_request, get_jwt_identity
from random import randint
from datetime import datetime
from bson.objectid import ObjectId
from ..models import db, user_collection, deleted_user_collection
from ..models.user import Manager, User, Buyer, Seller
import bcrypt
from ..views import permission_required
from ..views.permission import permissions, get_or_create_role


@manager_route.route('/<string:type>', strict_slashes=False, methods=['GET'])
def get_all_users(type):
    """
    Get all users
    ---
    tags:
      - Manager
    parameters:
      - in: path
        name: type
        type: string
        required: true
        description: Type of the user
    responses:
      200:
        description: List of users
        schema:
          type: teacher_response
          properties:
            teachers:
              type: array
              items:
                type: object
                properties:
                  full_name:
                    type: string
                    description: users full name
                  email:
                    type: string
                    description: users email
                  phone_number:
                    type: string
                    description: users phone number
      400:
        description: Bad request
        schema:
          type: error_response
          properties:
            error:
              type: string
              description: Error message
      404:
        description: No teachers found
        schema:
          type: error_response
          properties:
            error:
              type: string
              description: Error message
      500:
        description: Internal Server Error
        schema:
          type: error_response
          properties:
            error:
              type: string
              description: Error message
    """
    try:
      type = type.lower()
      if type == 'seller' or type == 'sellers':
        sellers = Seller.query.all()
        print(Seller.query.all())
        if not sellers:
          return jsonify({'error': f'No seller found'}), 404

        seller_data = []
        for seller in sellers:
          seller_data.append({
            'type': seller.type,
            'full_name': seller.full_name,
            'email': seller.email,
            'phone_number': seller.phone_number
          })

        return jsonify({'sellers': seller_data}), 200
      elif type == 'buyer' or type == 'buyers':
        buyers = Buyer.query.all()
        if not buyers:
          return jsonify({'error': f'No buyer found'}), 404

        buyer_data = []
        for buyer in buyers:
          buyer_data.append({
            'type': buyer.type,
            'full_name': buyer.full_name,
            'email': buyer.email,
            'phone_number': buyer.phone_number
          })

        return jsonify({'buyers': buyer_data}), 200
      
      elif type == 'all':
        users = User.query.all()
        if not users:
          return jsonify({'error': f'No user found'})
        
        user_data = []
        for user in users:
          user_data.append({
            'full_name': user.full_name,
            'email': user.email,
            'phone_number': user.phone_number,
            'type': user.type
          })

        return jsonify({'users': user_data}), 200
      
      else:
        return jsonify("Invalid type provided")

    except BadRequest as e:
      return jsonify({'error': str(e)}), 400
    except Exception as e:
      print(e)
      return jsonify({'error': str(e)}), 500


@manager_route.route('/<string:email>:', strict_slashes=False, methods=['GET'])
def get_specific_user(email):
    """
    Get a particular user's details
    ---
    tags:
      - Manager
    parameters:
      - in: path
        name: email
        type: string
        required: true
        description: email of the user
    responses:
      200:
        description: user details
        schema:
          id: user_response
          properties:
            full_name:
              type: string
              description: user full name
            email:
              type: string
              description: user email
            phone_number:
              type: string
              description: user phone number
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
      if not email:
        raise BadRequest('email not provided')
      
      user = User.query.filter_by(email=email).first()

      if not user:
        return jsonify({'error': 'User not found'}), 404
    
      return jsonify({
        'full_name': user.full_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'type': user.type
      }), 200

    except BadRequest as e:
      return jsonify({'error': str(e)}), 400
    except Exception as e:
      print(e)
      return jsonify({'error': str(e)}), 500

    
@manager_route.route('/<string:id>', strict_slashes=False, methods=['DELETE'])
# @jwt_required()
def delete_user(id):
    """
    Delete user
    ---
    tags:
      - Manager
    parameters:
      - in: path
        name: id
        required: true
        schema:
          type: string
          description: user ID
    responses:
      200:
        description: user deleted successfully
        schema:
          id: user_response
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
      if not id:
        raise BadRequest('No Id provided')

      print(id)
      # Try to find user in MongoDB first
      mongo_user = user_collection.find_one({
        '$or': [
          {'id': id},
          {'email': id},
        ]
      })

      user_id = None
      if mongo_user:
        user_id = mongo_user.get('id')
      if not user_id:
        # If not found in MongoDB, check SQL database
        user = User.query.filter(
          (User.id == id) |
          (User.email == id)
        ).first()
        if not user:
          return jsonify({'error': 'user not found'}), 404
        user_id = user.id
        print(user_id)

      # Get the specific user type instance
      user = User.query.get(user_id)
      if not user:
        return jsonify({'error': 'user not found'}), 404

      # Prepare user data for archiving
      user_dict = {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
      user_dict['deleted_at'] = datetime.utcnow()
      print(user_dict)

      # Delete from MongoDB and archive
      user_collection.delete_one({'fullName': user.full_name})
      deleted_user_collection.insert_one(user_dict)

      # Delete from SQL database
      db.session.delete(user)
      db.session.commit()

      return jsonify({'message': 'User deleted successfully'}), 200

    except BadRequest as e:
      return jsonify({'error': str(e)}), 400
    except IntegrityError:
      db.session.rollback()
      return jsonify({'error': 'Error deleting user due to integrity constraint', 'code': 'usr409'}), 409
    except Exception as e:
      db.session.rollback()
      print(f"Unexpected error: {str(e)}")
      return jsonify({'error': 'An unexpected error occurred'}), 500
