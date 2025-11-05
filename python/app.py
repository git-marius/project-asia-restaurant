from flask import Flask, jsonify
import mysql.connector
import os

app = Flask(__name__)

@app.route("/hello")
def hello():
    return jsonify({"message": "Flask laeuft ueber Nginx unter /api"})

@app.route("/db")
def db_test():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "mariadb"),
            user=os.getenv("DB_USER", "testuser"),
            password=os.getenv("DB_PASS", "testpass"),
            database=os.getenv("DB_NAME", "testdb")
        )
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "connected", "now": str(result[0])})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("FLASK_PORT", 5000))
