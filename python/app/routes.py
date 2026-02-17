from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta, timezone
from app.extensions.db import db
from app.models import Measurements

from scipy.stats import linregress

bp = Blueprint("main", __name__)

@bp.get("/")
def home():
    return render_template("dashboard.html")

def _dt_iso(dt: datetime) -> str:
    return dt.now(timezone.utc)

@bp.get("/api/dashboard")
def api_dashboard():
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    latest = (
        db.session.query(Measurements)
        .order_by(Measurements.timestamp.desc())
        .first()
    )

    rows_24h = (
        db.session.query(Measurements)
        #.filter(Measurements.timestamp >= since)
        .order_by(Measurements.timestamp.asc())
        .all()
    )


    xs = [r.persons for r in rows_24h if r.persons is not None and r.temperature is not None]
    ys = [r.temperature for r in rows_24h if r.persons is not None and r.temperature is not None]

    slope = intercept = r2 = None
    reg_line_points = []

    if len(xs) >= 2 and len(set(xs)) >= 2:
        res = linregress(xs, ys)
        slope = float(res.slope)
        intercept = float(res.intercept)
        r2 = float(res.rvalue ** 2)

        x_min, x_max = min(xs), max(xs)
        reg_line_points = [
            {"x": x_min, "y": slope * x_min + intercept},
            {"x": x_max, "y": slope * x_max + intercept},
        ]

    def predict(x):
        if slope is None or intercept is None:
            return None
        return float(slope * x + intercept)

    payload = {
        "meta": {"generated_at": _dt_iso(now)},
        "current": None if not latest else {
            "temperature": float(latest.temperature),
            "humidity": float(latest.humidity),
            "voc": float(latest.voc),
            "persons": int(latest.persons),
            "radar": bool(latest.radar),
            "timestamp": _dt_iso(latest.timestamp),
        },
        "line": {
            "points": [{"t": _dt_iso(r.timestamp), "temperature": float(r.temperature)} for r in rows_24h]
        },
        "scatter": {
            "points": [{"x": int(r.persons), "y": float(r.temperature)} for r in rows_24h]
        },
        "regression": {
            "slope": slope,
            "intercept": intercept,
            "r2": r2,
            "line_points": reg_line_points
        },
        "predictions": {
            "p0": predict(0),
            "p60": predict(60),
            "p120": predict(120)
        }
    }

    return jsonify(payload)
