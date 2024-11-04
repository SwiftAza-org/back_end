from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from . import db, BaseModel
from bson import ObjectId
from uuid import uuid4

# Association tables
manager = db.Table('swaz_manager',
    db.Column('swaz_id', db.String(36), db.ForeignKey('swaz.id'), primary_key=True),
    db.Column('owner_id', db.String(36), db.ForeignKey('managers.id'), primary_key=True)
)

user_roles = db.Table('user_roles',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id'), primary_key=True)
)

buyer_seller = db.Table('buyer_seller',
    db.Column('buyer_id', db.String(36), db.ForeignKey('buyers.id'), primary_key=True),
    db.Column('seller_id', db.String(36), db.ForeignKey('sellers.id'), primary_key=True)
)

role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.String(36), db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.String(36), db.ForeignKey('permissions.id'), primary_key=True)
)

user_wallet = db.Table('user_wallet',
db.Column('user_id', db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
db.Column('wallet_id', db.String(36), db.ForeignKey('wallets.id', ondelete='CASCADE'), primary_key=True)
)

class Swaz(BaseModel):
    __tablename__ = 'swaz'
    id = db.Column(db.String(36), primary_key=True)


class User(BaseModel):
    __tablename__ = 'users'

    full_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50))
    
    validated = db.Column(db.Boolean, default=False)
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    specific_permissions = db.relationship('UserSpecificPermission', back_populates='user')
    wallets = db.relationship('Wallet', secondary=user_wallet, back_populates='users')

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def set_password(self, password):
        from .. import bcrypt
        self.password = bcrypt.generate_password_hash(password)

    def validate_data(self, data):
        if not data:
            raise BadRequest('Missing Data')

        self.email = data.get('email')
        self.phone_number = data.get('phoneNumber')

        if not all([data.get('fullName'), data.get('password')]):
            raise BadRequest('Bad Request: User missing a credential')
                
        self.set_password(data.get('password'))
        self.full_name = data.get('fullName')

        return data.get('fullName')

    def has_permission(self, permission_code):
        # First, check role-based permissions
        role_based = any(permission.code == permission_code for role in self.roles for permission in role.permissions)
        
        # Then, check for user-specific overrides
        specific_perm = next((sp for sp in self.specific_permissions if sp.permission.code == permission_code), None)
        
        if specific_perm is not None:
            return specific_perm.is_granted
        
        return role_based


    def __repr__(self):
        return f"<User(full_name='{self.full_name}')>"


class Manager(User):
    __tablename__ = 'managers'

    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'manager',
    }

class Seller(User):
    __tablename__ = 'sellers'

    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'seller',
    }

class Buyer(User):
    __tablename__ = 'buyers'

    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'buyer',
    }

class Role(BaseModel):
    __tablename__ = 'roles'
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    permissions = db.relationship('Permission', secondary=role_permissions, back_populates='roles')

    def __repr__(self):
        return f"<Role(name='{self.name}', description='{self.description}')>"

class Permission(BaseModel):
    __tablename__ = 'permissions'
    
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary=role_permissions, back_populates='permissions')

    def __repr__(self):
        return f"<Permission(code='{self.code}', description='{self.description}')>"


class UserSpecificPermission(BaseModel):
    __tablename__ = 'user_specific_permissions'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), primary_key=True)
    is_granted = db.Column(db.Boolean, default=True)  # True to grant, False to revoke

    user = db.relationship('User', back_populates='specific_permissions')
    permission = db.relationship('Permission')

class Wallet(BaseModel):
    __tablename__ = 'wallets'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    pin = db.Column(db.String(255), nullable=False)

    users = db.relationship('User', back_populates='wallets')

    __mapper_args__ = {
        'polymorphic_identity': 'wallet'
    }

    def __init__(self, user_id, pin=None):
        from .. import bcrypt
        self.id = str(uuid4())
        self.user_id = user_id
        self.balance = 0.0
        self.pin = pin
    
    def add_balance(self, amount):
        self.balance += amount

    def subtract_balance(self, amount):
        if self.balance < amount:
            raise BadRequest('Insufficient Balance')
        self.balance -= amount
