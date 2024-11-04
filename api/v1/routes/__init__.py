from flask import Blueprint

root_route = Blueprint('root', __name__, url_prefix='/api/v1/')
auth_route = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
manage_user_route = Blueprint('user', __name__, url_prefix='/api/v1/user')
user_permission_route = Blueprint('user_permission', __name__, url_prefix='/api/v1/user_permission')
manager_route = Blueprint('manager', __name__, url_prefix='/api/v1/manager')
buyer_route = Blueprint('buyer', __name__, url_prefix='/api/v1/buyer')
seller_route = Blueprint('seller', __name__, url_prefix='/api/v1/seller')
wallet_route = Blueprint('wallet', __name__, url_prefix='/api/v1/wallet')


from . import home  # noqa: F401 E402
from . import auth  # noqa: F401 E402
from . import manager  # noqa: F401 E402
from . import buyer # noqa: F401 E402
from . import seller # noqa: F401 E402
from . import permission  # noqa: F401 E402
from . import wallet # noqa : F401 E402
