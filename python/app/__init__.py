from flask import Flask
from .config import Config
from .extensions import db, migrate
from .routes import bp
from .seed import seed
import logging

def create_app():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
        
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    
    @flask_app.cli.command("seed")
    def seed_command():
        seed()
        print("Seed complete")

    with flask_app.app_context():
        from . import models

    flask_app.register_blueprint(bp)

    return flask_app
