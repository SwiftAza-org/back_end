from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from . import db, BaseModel
from bson import ObjectId
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import validates

# Association tables

user_wallet = db.Table('user_wallet',
db.Column('user_id', db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
db.Column('wallet_id', db.String(36), db.ForeignKey('wallets.id', ondelete='CASCADE'), primary_key=True)
)



class User(BaseModel):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    full_name = db.Column(db.String(80), nullable=False)
    card_number = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(120), nullable=True)
    account_type = db.Column(db.String(120), nullable=False)
    wallets = db.relationship('Wallet', secondary=user_wallet, back_populates='users')
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, full_name=None, card_number=None, account_type=None, phone_number=None):
        self.id = str(uuid4())
        self.full_name = full_name
        self.card_number = card_number
        self.account_type = account_type
        self.phone_number = phone_number
        self.balance = 0.0

    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }

    def set_password(self, password):
        from .. import bcrypt
        self.password = bcrypt.generate_password_hash(password)

    def validate_data(self, data):
        if not data:
            raise BadRequest('Missing Data')

        self.card_number = data.get('card_number')
        self.phone_number = data.get('phoneNumber')

        if not all([data.get('fullName'), data.get('card_number'), data.get('account_type')]):
            raise BadRequest('Bad Request: User missing a credential')
                
        self.full_name = data.get('fullName')
        self.account_type = data.get('account_type')

        return data.get('fullName')


    def __repr__(self):
        return f"<User(full_name='{self.full_name}')>"


class Wallet(BaseModel):
    __tablename__ = 'wallets'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    card_number = db.Column(db.String(120), nullable=False)
    user_account_type = db.relationship('User', secondary=user_wallet, back_populates='wallets')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    users = db.relationship('User', back_populates='wallets')

    __mapper_args__ = {
        'polymorphic_identity': 'wallet'
    }

    def __init__(self, user_id, card_number=None):
        from .. import bcrypt
        self.id = str(uuid4())
        self.user_id = user_id
        self.balance = 0.0
        self.card_number = card_number
    
    def add_balance(self, amount):
        self.balance += amount

    def subtract_balance(self, amount):
        if self.balance < amount:
            raise BadRequest('Insufficient Balance')
        self.balance -= amount
