from datetime import datetime, timedelta, timezone

from flask import Blueprint, abort, jsonify, redirect, render_template, request
from scipy.stats import linregress

from app.logic.storage.s3 import create_presigned_video_url
from app.models.repositories import get_latest, get_since, get_video_recording, get_video_recordings

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


def _video_payload(video):
    """Serialisiert einen Video-Datensatz für das Dashboard."""
    return {
        "id": video.id,
        "recorded_at": _dt_iso(video.recorded_at),
        "duration_seconds": int(video.duration_seconds),
        "bucket": video.bucket,
        "object_key": video.object_key,
        "content_type": video.content_type,
        "size_bytes": video.size_bytes,
        "status": video.status,
        "error_message": video.error_message,
        "created_at": _dt_iso(video.created_at),
        "play_url": f"/api/videos/{video.id}/play" if video.status == "stored" else None,
    }


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

    latest = get_latest()
    rows_24h = get_since(since)

    xs, ys = [], []
    scatter_points = []
    line_points = []

    for r in rows_24h:
        line_points.append({"t": _dt_iso(r.timestamp), "temperature": float(r.temperature)})

        if r.persons is not None and r.temperature is not None:
            xs.append(int(r.persons))
            ys.append(float(r.temperature))
            scatter_points.append({"x": int(r.persons), "y": float(r.temperature)})

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

    def predict(x: int):
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


@bp.get("/api/videos")
def api_videos():
    """Liefert die neuesten Videoaufnahmen fürs Dashboard."""
    raw_limit = request.args.get("limit", "25")
    try:
        # Limit begrenzen, damit das Dashboard nicht versehentlich zu viele DB-Zeilen lädt.
        limit = max(1, min(int(raw_limit), 100))
    except ValueError:
        limit = 25

    videos = get_video_recordings(limit=limit)
    return jsonify({
        "meta": {"generated_at": _dt_iso(datetime.now(timezone.utc)), "limit": limit},
        "videos": [_video_payload(video) for video in videos],
    })


@bp.get("/api/videos/<int:video_id>/play")
def play_video(video_id: int):
    """Leitet auf eine kurzlebige presigned URL für das private S3-Objekt weiter."""
    video = get_video_recording(video_id)
    if video is None or video.status != "stored":
        abort(404)

    try:
        # Bucket bleibt privat; der Browser bekommt nur eine kurz gültige S3-URL.
        url = create_presigned_video_url(video.bucket, video.object_key)
    except Exception:
        abort(502)

    return redirect(url, code=302)
