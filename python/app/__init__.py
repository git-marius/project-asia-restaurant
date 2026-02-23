from flask import Flask
from .config import Config
from .extensions import db, migrate
from .routes import bp
from .seed import seed
import logging


def create_app():
    """App-Factory: erstellt und konfiguriert die Flask-Anwendung (DB, Routes, CLI)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)  # Config (z. B. DB-URI) laden

    db.init_app(flask_app)               # SQLAlchemy an Flask hängen
    migrate.init_app(flask_app, db)      # Alembic/Flask-Migrate initialisieren

    @flask_app.cli.command("seed")
    def seed_command():
        """CLI-Befehl: flask seed -> füllt die Datenbank mit Seed-Daten."""
        seed()
        print("Seed complete")

    # Models im App-Context importieren, damit SQLAlchemy sie kennt
    with flask_app.app_context():
        from . import models  # noqa: F401

    flask_app.register_blueprint(bp)     # Routen registrieren
    return flask_app