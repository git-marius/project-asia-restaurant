from flask import Flask
from .config import Config
from .extensions import db, migrate
from .routes import bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from . import models

    app.register_blueprint(bp)

    return app
