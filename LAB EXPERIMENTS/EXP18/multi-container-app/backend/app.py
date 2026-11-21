import os
from flask import Flask, jsonify, request

app = Flask(__name__)
NOTES_MEM = []     # used when no database is configured (local testing)


def db():
    """Connect to PostgreSQL when DB_HOST is set (Kubernetes), otherwise return None."""
    host = os.getenv("DB_HOST")
    if not host:
        return None
    import psycopg2
    return psycopg2.connect(host=host, dbname=os.getenv("DB_NAME", "notes"),
                            user=os.getenv("DB_USER", "notes"), password=os.getenv("DB_PASSWORD", "notes"))


def init_db():
    conn = db()
    if conn:
        with conn, conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, text TEXT NOT NULL)")
        conn.close()


@app.route("/api/health")
def health():
    return jsonify(status="ok", database="postgres" if os.getenv("DB_HOST") else "in-memory")


@app.route("/api/notes", methods=["GET", "POST"])
def notes():
    conn = db()
    if request.method == "POST":
        text = (request.get_json(silent=True) or {}).get("text", "").strip()
        if not text:
            return jsonify(error="text is required"), 400
        if conn:
            with conn, conn.cursor() as cur:
                cur.execute("INSERT INTO notes (text) VALUES (%s)", (text,))
        else:
            NOTES_MEM.append(text)
        return jsonify(saved=text), 201
    if conn:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT text FROM notes ORDER BY id")
            return jsonify([r[0] for r in cur.fetchall()])
    return jsonify(NOTES_MEM)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
