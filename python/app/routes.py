from flask import Blueprint, jsonify, render_template
from sqlalchemy import text
from .extensions import db

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    return render_template("index.html")


@bp.get("/db")
def db_test():
    try:
        now = db.session.execute(text("SELECT NOW();")).scalar()
        return jsonify({"status": "connected", "now": str(now)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
