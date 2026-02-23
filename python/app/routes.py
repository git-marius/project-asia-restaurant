from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta, timezone
from app.extensions.db import db
from app.models import Measurements
from scipy.stats import linregress
from app.models.repositories import get_latest, get_since

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    """Liefert die Dashboard-Webseite (HTML) aus."""
    return render_template("dashboard.html")


def _dt_iso(dt: datetime) -> str:
    """Konvertiert ein Datum sicher nach UTC und gibt es als ISO-String zurück."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


@bp.get("/api/dashboard")
def api_dashboard():
    """
    API-Endpunkt fürs Dashboard:
    - Holt den neuesten Messwert + alle Messwerte der letzten 24h
    - Baut Datenpunkte für Linienchart (Temperatur über Zeit) und Scatterplot (Personen vs Temperatur)
    - Rechnet eine lineare Regression (Trendlinie) inkl. R² und macht Beispiel-Vorhersagen
    - Gibt alles als JSON zurück
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    latest = get_latest()          # letzter Messdatensatz
    rows_24h = get_since(since)    # Messdaten der letzten 24 Stunden

    xs, ys = [], []
    scatter_points = []
    line_points = []

    for r in rows_24h:
        # Linie: Temperatur über Zeit
        line_points.append({"t": _dt_iso(r.timestamp), "temperature": float(r.temperature)})

        # Scatter: Personenanzahl (x) gegen Temperatur (y)
        if r.persons is not None and r.temperature is not None:
            xs.append(int(r.persons))
            ys.append(float(r.temperature))
            scatter_points.append({"x": int(r.persons), "y": float(r.temperature)})

    slope = intercept = r2 = None
    reg_line_points = []

    # Regression nur, wenn genug verschiedene x-Werte vorhanden sind
    if len(xs) >= 2 and len(set(xs)) >= 2:
        res = linregress(xs, ys)
        slope = float(res.slope)
        intercept = float(res.intercept)
        r2 = float(res.rvalue ** 2)

        # Trendlinie nur mit 2 Punkten (min/max) fürs Zeichnen
        x_min, x_max = min(xs), max(xs)
        reg_line_points = [
            {"x": x_min, "y": slope * x_min + intercept},
            {"x": x_max, "y": slope * x_max + intercept},
        ]

    def predict(x: int):
        """Gibt die geschätzte Temperatur für eine Personenanzahl zurück (oder None ohne Regression)."""
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
        "line": {"points": line_points},
        "scatter": {"points": scatter_points},
        "regression": {
            "slope": slope,
            "intercept": intercept,
            "r2": r2,
            "line_points": reg_line_points,
        },
        "predictions": {
            "p0": predict(0),
            "p60": predict(60),
            "p120": predict(120),
        },
    }

    return jsonify(payload)