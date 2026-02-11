from flask import Flask
from .config import Config
from .extensions import db, migrate
from .routes import bp


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    with flask_app.app_context():
        from . import models

    flask_app.register_blueprint(bp)

    return flask_app
