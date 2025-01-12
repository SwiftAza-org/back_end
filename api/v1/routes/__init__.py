from flask import Blueprint

root_route = Blueprint('root', __name__, url_prefix='/api/v1/')
auth_route = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
user_route = Blueprint('user', __name__, url_prefix='/api/v1/user')

from . import home  # noqa: F401 E402
from . import auth  # noqa: F401 E402
from . import user # noqa: F401 E402
