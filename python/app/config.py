import os
from urllib.parse import quote_plus


class Config:
    """Zentrale App-Konfiguration (v. a. Datenbank-Einstellungen über Umgebungsvariablen)."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # spart Overhead (keine Änderungsverfolgung durch SQLAlchemy)

    # DB-Zugangsdaten aus Environment, mit sinnvollen Defaults für lokale/dev Setups
    DB_HOST = os.getenv("DB_HOST", "mariadb")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "testuser")
    DB_PASS = os.getenv("DB_PASS", "testpass")
    DB_NAME = os.getenv("DB_NAME", "testdb")

    # Verbindungs-URL für SQLAlchemy (Passwort wird URL-sicher codiert, z. B. bei Sonderzeichen)
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://"
        f"{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )