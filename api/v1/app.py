from os import environ
from . import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

app = create_app(environ.get('FLASK_ENV', 'production'))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
  