"""App entrypoint."""

import os
import secrets
import time
from flask import Flask, g, session

def create_app(test_config=None):
    """Create app instance."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    @app.before_request
    def ensure_csrf_token():
        """Create CSRF token if doesn't exist."""
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)

    @app.before_request
    def before_request():
        """Start timer before app request."""
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Stop timer after request."""
        start_time = getattr(g, 'start_time', None)
        if start_time is not None:
            elapsed = round(time.time() - start_time, 2)
            print(f"elapsed time: {elapsed} s")
        return response

    from . import db  # pylint: disable=import-outside-toplevel
    db.init_app(app)

    from .auth_routes import bp as auth_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(auth_bp)

    from .movies_routes import bp as movies_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(movies_bp)

    return app
