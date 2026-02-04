import os
from urllib.parse import quote_plus


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_HOST = os.getenv("DB_HOST", "mariadb")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "testuser")
    DB_PASS = os.getenv("DB_PASS", "testpass")
    DB_NAME = os.getenv("DB_NAME", "testdb")

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://"
        f"{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
