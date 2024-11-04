from flask import jsonify, request, make_response
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from random import randint
from datetime import datetime
from bson.objectid import ObjectId
from ..models import db, user_collection, deleted_user_collection
from ..models.user import User
from flask_mail import Mail, Message
from flask import current_app, url_for
from random import randint
import time


all_code = {}
def generate_verification_code(email):
    """
    Generate a random verification code and store it with an expiration time
    """
    veri_code = randint(1001, 9999)
    expiration_time = time.time() + 60  # 60 seconds from now
    all_code.update({email: [veri_code, expiration_time]})
    return veri_code
    

def is_verification_code_valid(email, code):
    """
    Check if the verification code is valid and not expired
    """
    if email not in all_code:
        print(f"Email '{email}' not found in verification data.")
        return False

    stored_code, expiration_time = all_code[email]  # Unpack the tuple

    print(f"Stored expiration time: {expiration_time}, Code: {stored_code}")
    print(f"Current time: {time.time()}")
    print(all_code)

    # Compare code and expiration time
    if time.time() < expiration_time and int(stored_code) == int(code):
        return True
    return False


def cleanup_expired_codes():
    """
    Cleanup expired verification codes
    """
    for email in list(all_code.keys()):
        _, expiration_time = all_code[email]
        if time.time() > expiration_time:
            del all_code[email]


def send_ver_code(email):
      """
      Send verification code upon succesful signup
      """
      user = User()

      the_user = user.query.filter_by(email=email).first()
      print(email)
      print(the_user)
      full_name = the_user.full_name
      print(full_name)

      default_sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@yourapp.com')
      veri_code = generate_verification_code(email)
      msg = Message(
            subject='Welcome to SwiftAza. Copy your verificaton code',
            sender=default_sender,
            recipients=[email],
            body=f"Hello {full_name},\n\n"
            f"You have just created an account with SwiftAza.\n"
            f"Here is your Verification code\n"

            f"VERIFICATION CODE: {veri_code}\n\n"

            f"Thank You"
        )
      mail = Mail(current_app)
      mail.send(msg)

