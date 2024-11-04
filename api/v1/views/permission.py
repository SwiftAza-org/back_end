from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, user_collection
from ..models.user import Role, Permission, User, Manager, Buyer, Seller

data_type = {
        'manager': Manager,
        'buyer': Buyer,
        'seller': Seller,
    }

from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy.exc import SQLAlchemyError

def get_or_create_role(role_name, permissions, user=None, user_type=None):
    try:
        # Start a transaction
        db.session.begin_nested()

        # Find existing role or create a new one
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role()
            role.name = role_name
            db.session.add(role)
        
        # Process permissions
        for perm_code in permissions:
            perm = Permission.query.filter_by(code=perm_code).first()
            if not perm:
                perm = Permission()
                perm.code = perm_code
                perm.description = f"{perm_code} permission"
                db.session.add(perm)
            
            if perm not in role.permissions:
                role.permissions.append(perm)
        
        # Update user's role if provided
        if user:
            if user_type:
                if user_type not in data_type:
                    raise ValueError("Invalid user type")
                if not isinstance(user, data_type[user_type]):
                    user = data_type[user_type].query.get(user)
            else:
                if not isinstance(user, User):
                    user = User.query.get(user)
            
            if user:
                user.roles = [role]  # Assuming a user can have multiple roles
        
        # Commit the transaction
        # db.session.commit()
        return role

    except (DetachedInstanceError, SQLAlchemyError) as e:
        db.session.rollback()
        print(f"Error in get_or_create_role: {str(e)}")
        # Optionally, re-raise the exception or handle it as needed
        # raise



def get_user_permissions(email):

    user = user_collection.find_one({'email': email})
    user = data_type['type'].query.filter_by(email=email).first()
    if not user:
        raise ValueError("User not found")

    role = Role.query.get(user.role_id)
    if not role:
        return []

    permissions = [permission.code for permission in role.permissions]
    return permissions


def remove_permission_from_user(user_id, permission_code):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    # Get the role of the user
    role = Role.query.get(user.role_id)
    if not role:
        raise ValueError("Role not found")

    # Find the permission to remove
    permission = Permission.query.filter_by(code=permission_code).first()
    if not permission:
        raise ValueError("Permission not found")

    # Remove permission from the role
    if permission in role.permissions:
        role.permissions.remove(permission)
        db.session.commit()
        return True
    return False

permissions = {
    "admin": [
        "adm101",
        "adm102",
        "adm103",
        "adm104",
        "adm105",
        "adm106",
        "adm107",
        "adm108"
    ],
    "buyer": [
        "buy101",
        "buy102",
        "buy103",
        "buy104",
        "buy105",
        "buy106",
        "buy107",
        "buy108"
    ],
    "seller": [
        "sel101",
        "sel102",
        "sel103",
        "sel104",
        "sel105",
        "sel106",
        "sel107",
        "sel108"
    ],
}

def permission_required(required_permissions):
    """
    Decorator to ensure that the current user has the necessary permissions.
    
    This function first checks if the user exists in MongoDB. If not, it checks MySQL.
    The permissions are then checked based on the roles in MySQL or directly from MongoDB.
    
    :param required_permissions: List of permissions required to access the endpoint
    :return: Decorated function
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # Get the current user ID from the JWT token
                current_user_id = get_jwt_identity()

                # First, try to get the user from MongoDB
                user_mongo = user_collection.find_one({'id': current_user_id})
                
                if user_mongo:
                    user_type = user_mongo.get('type')
                    email = user_mongo.get('email')

                    # Print MongoDB user details and permissions
                    mongo_permissions = set(user_mongo.get('permissions', []))
                    print(f"MongoDB User Permissions: {mongo_permissions}")
                else:
                    # If not found in MongoDB, try SQL database
                    user_sql = User.query.get(current_user_id)
                    if not user_sql:
                        return jsonify({'error': 'User not found'}), 404
                    
                    # Determine the user type based on their model in MySQL
                    user_type = next((k for k, v in data_type.items() if isinstance(user_sql, v)), None)
                    email = user_sql.email

                    # Print MySQL user details
                    print(f"MySQL User: {email} (Type: {user_type})")
                
                if not user_type or not email:
                    return jsonify({'error': 'Invalid user data'}), 400

                # Get user details from MySQL using the determined type and email
                user = data_type[user_type].query.filter(
                    (data_type[user_type].email == email)
                ).first()
                
                if not user:
                    return jsonify({'error': 'User not found in SQL database'}), 404

                # Gather permissions from MySQL
                user_permissions = set()
                for role in user.roles:
                    user_permissions.update(permission.code for permission in role.permissions)

                # Print MySQL user permissions
                print(f"MySQL User Permissions: {user_permissions}")
                
                # Check for required permissions in MySQL
                if not any(perm in user_permissions for perm in required_permissions):
                    # If not found in MySQL, check MongoDB for permissions
                    mongo_user = user_collection.find_one({'id': current_user_id})
                    if mongo_user:
                        mongo_permissions = set(mongo_user.get('permissions', []))
                        print(f"MongoDB Permissions (recheck): {mongo_permissions}")

                        if not any(perm in mongo_permissions for perm in required_permissions):
                            return jsonify({'error': 'Permission denied'}), 403
                    else:
                        return jsonify({'error': 'Permission denied'}), 403

                # If permissions check passes, proceed to the protected route
                return f(*args, **kwargs)
            
            except Exception as e:
                # Cabuy any unexpected exceptions and return a 500 error
                return jsonify({'error': str(e)}), 500
        
        return decorated_function
    return decorator
