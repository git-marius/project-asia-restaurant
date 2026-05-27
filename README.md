# Project Asia Restaurant 🍜🌡️

Schulprojekt: Sensor-/IoT-Dashboard für ein (simuliertes) Asia-Restaurant – mit Messwerterfassung, Datenbank, Web-GUI und einfacher Auswertung (lineare Regression).

---

## Inhalt
- [Projektidee](#projektidee)
- [Features](#features)
- [Technologien](#technologien)
- [Architektur (High Level)](#architektur-high-level)
- [Neu: Videoaufnahmen bei Bewegung](#neu-videoaufnahmen-bei-bewegung)
- [Setup & Start (Docker)](#setup--start-docker)
- [Konfiguration (.env)](#konfiguration-env)
- [Benutzung](#benutzung)
- [Ordner- & Dateistruktur](#ordner--dateistruktur)
- [Bilder / Dokumentation](#bilder--dokumentation)
- [Troubleshooting](#troubleshooting)
---

## Projektidee
In einem (simulierten) Asia-Restaurant werden Umwelt- und Belegungsdaten erfasst (z. B. Temperatur, Luftfeuchtigkeit, VOC und Personen/Radar).  
Diese Messwerte werden gespeichert und über ein Web-Dashboard visualisiert.

Zusätzlich wird eine einfache **lineare Regression** berechnet (z. B. Zusammenhang „Personen ↔ Temperatur“) und als Diagramm + Kennzahlen (Steigung, Intercept, R²) dargestellt.

---

## Features
- Web-Dashboard (Flask) mit Kacheln & Diagrammen (z. B. Verlauf der letzten 24h)
- Videobereich mit bewegungsausgelösten MP4-Aufnahmen aus MinIO/S3
- API-Endpoint liefert JSON für das Dashboard (z. B. aktuelle Werte, Verlauf, Regression)
- MariaDB zur Speicherung von Messwerten (über ORM)
- Celery Worker + Celery Beat für periodische Jobs (z. B. Daten holen/aufbereiten)
- MinIO als lokaler S3-kompatibler Objektspeicher für Videoaufnahmen
- Nginx als Reverse Proxy vor Flask
- Optional: phpMyAdmin zur Ansicht/Debugging der Datenbank

---

## Technologien

### Backend
- Python (Container)
- Flask (Webserver)
- SQLAlchemy (ORM) + Migrationen (z. B. Flask-Migrate)
- Celery (Jobs/Queue)
- Redis (Broker/Backend für Celery)

### Infrastruktur / Datenbank
- MariaDB
- MinIO / S3-kompatibler Objektspeicher
- Nginx (Reverse Proxy)
- Docker + Docker Compose

### Datenanalyse
- Lineare Regression (z. B. mit SciPy)

### Hardware/Sensorik (je nach Aufbau)
- BME680 (Temperatur/Luftfeuchte/VOC) über I2C (z. B. Raspberry Pi / Linux)
- PIR-Bewegungssensor und Kamera für bewegungsausgelöste Videoaufnahmen
- Optional: Radar/Belegungssensor oder simulierte Personenwerte

---

## Architektur (High Level)
Docker Compose startet mehrere Services:
- `mariadb` (persistente DB)
- `redis` (Celery Broker/Backend)
- `flask` (Web-App)
- `celery_worker` (führt Jobs aus)
- `celery_beat` (plant Jobs)
- `minio` (S3-kompatibler Speicher für Videos)
- `minio_init` (legt den Video-Bucket an)
- `nginx` (Proxy)
- `phpmyadmin` (optional)

---

## Neu: Videoaufnahmen bei Bewegung
- Celery Beat startet jede Sekunde den Task `videos.capture_on_motion`.
- Der Task liest den PIR-Bewegungssensor und nimmt pro zusammenhängender Bewegung genau einen MP4-Clip auf.
- Redis wird als Lock- und Status-Speicher genutzt, damit keine überlappenden Clips entstehen.
- Die MP4-Datei wird nach MinIO/S3 hochgeladen; MariaDB speichert nur die Metadaten.
- Das Dashboard hat einen neuen Bereich `Videos` mit Verlauf, Zeitstempel und HTML5-Player.

### Technischer Ablauf
1. `celery_beat` triggert `videos.capture_on_motion` im Sekundenintervall.
2. `celery_worker` prüft Bewegung über `motion_sensor_infrared.motion_detected()`.
3. Bei Bewegung setzt der Worker `videos:capture-lock` und `videos:motion-active` in Redis.
4. `capture_mp4()` erzeugt einen Clip. Standard ist `raspivid` + `ffmpeg`; alternativ kann `VIDEO_CAPTURE_COMMAND` gesetzt werden.
5. `upload_video_file()` lädt das Video in den privaten S3-Bucket, z. B. `videos/YYYY/MM/DD/<timestamp>_<uuid>.mp4`.
6. `VideoRecording` speichert `recorded_at`, `duration_seconds`, `bucket`, `object_key`, `size_bytes` und `status`.
7. `GET /api/videos` liefert den Verlauf; `GET /api/videos/<id>/play` erzeugt eine kurzlebige presigned URL.

---

## Setup & Start (Docker)

### Voraussetzungen
- Docker installiert
- Docker Compose installiert
- UV installiert

### 1) Repo klonen
```bash
git clone https://github.com/git-marius/project-asia-restaurant.git
cd project-asia-restaurant
```

### 2) `.env` anlegen
```bash
cp .env.example .env
```

### 3) Virtual Environment aufsetzen und installieren
```bash
cd python
uv venv
uv sync
```

### 4) Container starten
```bash
docker compose up --build
```

Danach erreichbar (je nach Ports aus `.env`):
- Web-App: `http://localhost:<WEB_PORT>` (oft `http://localhost:80`)
- MinIO Console: `http://localhost:<MINIO_CONSOLE_PORT>` (oft `http://localhost:9001`)
- phpMyAdmin (optional): `http://localhost:<PHPMYADMIN_PORT>` (oft `http://localhost:8081`)

### Lokaler Start: empfohlene Commands
Wenn du das Projekt lokal frisch starten willst:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
docker compose exec flask uv run flask db upgrade
docker compose exec flask uv run flask seed
```

Logs prüfen:

```bash
docker compose logs -f flask celery_worker celery_beat minio_init
```

MinIO öffnen:
- Console: `http://localhost:9001`
- Login aus `.env`: `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`
- Bucket: `restaurant-videos` oder Wert aus `S3_BUCKET`

Für einen lokalen Test ohne Raspberry-Pi-Kamera kannst du temporär einen Testclip mit `ffmpeg` erzeugen:

```bash
docker compose exec redis redis-cli del videos:motion-active videos:capture-lock
docker compose exec \
  -e VIDEO_CAPTURE_COMMAND='ffmpeg -y -f lavfi -i testsrc=size=320x240:rate=10 -t {duration_seconds} -pix_fmt yuv420p {output}' \
  flask uv run python -c "from app import create_app; from app.tasks import tasks; app=create_app(); tasks._read_motion_sensor=lambda: True; ctx=app.app_context(); ctx.push(); print(tasks.capture_on_motion.run()); ctx.pop()"
```

Danach im Dashboard den Tab `Videos` öffnen.

---

## Konfiguration (.env)
Die wichtigsten Variablen stehen in `.env.example`. Typisch sind:
- `PROJECT_NAME` – Prefix/Name für Container
- `WEB_PORT` – Port für Nginx (extern)
- `FLASK_PORT` – interner Flask Port
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` – MariaDB Zugangsdaten
- `PHPMYADMIN_PORT` – Port für phpMyAdmin
- `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT` – MinIO Zugang/Ports
- `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_PUBLIC_ENDPOINT_URL`, `S3_REGION` – S3-Ziel für Videoobjekte
- `VIDEO_CAPTURE_DURATION_SECONDS`, `VIDEO_CAPTURE_COMMAND` – Videoaufnahme-Dauer und optionaler Capture-Befehl

> Hinweis: Wenn Ports bereits belegt sind, ändere `WEB_PORT` oder `PHPMYADMIN_PORT`.

---

## Benutzung

### Wichtig: Migrationen ausführen, bevor du seedest
Bevor Demo-Daten geseedet werden, muss die Datenbank auf dem **aktuellen Stand** sein.  
Führe daher **zuerst** das Upgrade der Migrationen aus:

```bash
docker compose exec flask uv run flask db upgrade
```

Danach kannst du seeden.

### Datenbank seeden (Demo-Daten)
Für eine schnelle Demo kann die Datenbank mit Beispiel-Messwerten befüllt werden.

> Hinweis: Das Seeding **fügt** Datensätze hinzu (es löscht keine bestehenden). Bei erneutem Ausführen entstehen ggf. Duplikate.

```bash
docker compose exec flask uv run flask seed
```

Danach das Dashboard neu laden – die Charts/Regression sollten Daten anzeigen.

### Web-Dashboard
- Öffne die Startseite im Browser (Root `/`) um das Dashboard zu sehen.

### API
- `GET /api/dashboard` liefert typischerweise:
  - aktuelle Werte (z. B. Temperatur, Feuchte, VOC, Personen)
  - Verlaufspunkte (z. B. letzte 24h)
  - Scatterdaten + Regression (Steigung, Achsenabschnitt, R²)
  - ggf. einfache Vorhersagen (z. B. Temperatur bei 0/60/120 Personen)
- `GET /api/videos?limit=25` liefert den Videoverlauf.
- `GET /api/videos/<id>/play` leitet auf eine kurzlebige private S3-Playback-URL weiter.

---

## Ordner- & Dateistruktur
> Kurzüberblick (kann sich je nach Projektstand ändern)

```text
project-asia-restaurant/
├─ docker-compose.yml
├─ .env.example
├─ nginx/
│  └─ nginx.conf
└─ python/
   ├─ Dockerfile
   ├─ pyproject.toml
   ├─ uv.lock
   ├─ wsgi.py
   └─ app/
      ├─ __init__.py
      ├─ config.py
      ├─ routes.py
      ├─ celery_app.py
      ├─ extensions/
      │  ├─ __init__.py
      │  ├─ db.py
      │  └─ migrate.py
      ├─ models/
      │  ├─ __init__.py
      │  ├─ measurements.py
      │  └─ repositories.py
      └─ templates/
         ├─ base.html
         └─ dashboard.html
```

**Wichtige Dateien**
- `docker-compose.yml`: definiert alle Services (DB, Redis, Flask, Celery, Nginx, phpMyAdmin)
- `nginx/nginx.conf`: Reverse-Proxy-Konfiguration
- `python/Dockerfile`: baut das Python-Image
- `python/app/routes.py`: Routen für Dashboard & API (inkl. Regression)
- `python/app/models/*`: Datenmodelle / Tabellen
- `python/app/tasks/tasks.py`: Celery Tasks für Messwerte, Cleanup und Videoaufnahme
- `python/app/logic/storage/s3.py`: S3/MinIO Upload und presigned Playback URLs
- `python/app/templates/*`: HTML Templates

---

## Bilder / Dokumentation

### Schaltung / Verdrahtung

![Schaltplan / Verdrahtung](docs/images/schaltung.jpeg)
![Schaltplan / Verdrahtung (Camera)](docs/images/schaltung2.jpg)

### GUI / Dashboard

![Dashboard Screenshot](docs/images/gui-dashboard.png)
![Regression Screenshot](docs/images/gui-regression.png)

---

## Troubleshooting
- **Ports belegt**: `WEB_PORT` oder `PHPMYADMIN_PORT` in `.env` ändern und neu starten.
- **DB-Probleme**: `MYSQL_*` Werte prüfen und schauen ob `mariadb` läuft (`docker compose ps`).
- **Celery läuft nicht**: Redis-Service prüfen (Celery nutzt Redis als Broker/Backend).
- **Keine Videos lokal**: Ohne Raspberry-Pi-Hardware setzt der Sensor keine Bewegung. Nutze den lokalen `ffmpeg`-Testclip-Befehl oben.
- **Video nicht abspielbar**: `S3_PUBLIC_ENDPOINT_URL` muss vom Browser erreichbar sein, lokal meistens `http://localhost:9000`.
- **Build/Dependencies**: `docker compose build --no-cache` probieren.
