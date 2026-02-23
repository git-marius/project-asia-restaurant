"""
Einstiegspunkt der Anwendung.

Dieses Skript erstellt die Flask-App-Instanz über die Factory-Funktion `create_app()`.
So bleibt die Konfiguration/Initialisierung sauber von der Ausführung getrennt.
"""

from app import create_app  # Importiert die App-Factory (erstellt und konfiguriert die Flask-Anwendung)

# Flask-Anwendung erstellen (App-Instanz wird mit allen Blueprints/Configs initialisiert)
flask_app = create_app()