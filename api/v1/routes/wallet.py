from . import wallet_route
from flask import jsonify, request, make_response
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity
from random import randint
from datetime import datetime
from bson.objectid import ObjectId
from ..models import db, user_collection, deleted_user_collection
from ..models.user import Wallet
from ..views import permission_required
import bcrypt


@wallet_route.route('/wallet', strict_slashes=False, methods=['POST'])
def create_pin():
    """
    Create or update a wallet PIN
    ---
    tags:
        - Wallet
    summary: Create or update a wallet PIN
    description: Create a new wallet or update the existing wallet PIN for a user
    parameters:
        - in: body
          name: wallet
          description: The wallet information
          required: true
          schema:
            type: object
            required:
                - userId
                - pin
            properties:
                userId:
                    type: string
                    description: The ID of the user
                pin:
                    type: string
                    description: The PIN for the wallet
    responses:
        201:
            description: Wallet created or updated successfully
            schema:
                type: object
                properties:
                    message:
                        type: string
                        description: Success message
                    wallet:
                        type: object
                        properties:
                            user_id:
                                type: string
                                description: The ID of the user
                            wallet_id:
                                type: string
                                description: The ID of the wallet
                            wallet_pin:
                                type: string
                                description: The PIN of the wallet
            examples:
                application/json:
                    {
                        "message": "Wallet created successfully",
                        "wallet": {
                            "user_id": "12345",
                            "wallet_id": "67890",
                            "wallet_pin": "1234"
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
                        "error": "Missing userId or pin"
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
                        "error": "Database Integrity Error",
                        "code": "db409"
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
        from .. import bcrypt
        if not data:
            raise BadRequest('Missing Data')

        user_id = data.get('userId')
        pin = bcrypt.generate_password_hash(data.get('pin'))

        if not user_id or not pin:
            raise BadRequest('Missing userId or pin')

        existing_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not existing_wallet:
            wallet = Wallet(user_id=user_id, pin=pin)  # Pass pin here
        else:
            wallet = existing_wallet
            wallet.pin = pin
        

        db.session.add(wallet)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        raise BadRequest('Database Integrity Error')

    user = user_collection.find_one({'id': user_id})
    if not user:
        raise BadRequest('User not found')

    user['wallet_id'] = str(wallet.id)
    user_collection.update_one({'id': user_id}, {'$set': user})

    response = jsonify({
        'message': 'Wallet created successfully',
        'wallet': {
            'user_id': user_id,
            'wallet_id': str(wallet.id),
            'wallet_pin': wallet.pin,
        }
    })

    return response, 201

