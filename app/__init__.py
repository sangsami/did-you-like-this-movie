"""App entrypoint."""

import os
import time
from flask import Flask, g

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
    def before_request():
        """Start timer before app request."""
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Stop timer after request."""
        elapsed = round(time.time() - g.start_time, 2)
        print(f"elapsed time: {elapsed} s")
        return response

    from . import db  # pylint: disable=import-outside-toplevel
    db.init_app(app)

    from .auth import bp as auth_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(auth_bp)

    from .movies import bp as movies_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(movies_bp)
    app.add_url_rule('/', endpoint='index')

    return app
