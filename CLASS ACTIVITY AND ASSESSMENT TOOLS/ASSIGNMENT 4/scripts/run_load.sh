#!/usr/bin/env bash
# Start an isolated server on a throw-away database, run the bounded load experiment, stop it.
set -eu
cd "$(dirname "$0")/.."
PORT="${PORT:-18082}"; SECS="${SECS:-10}"
export SECRET_KEY="$(python -c 'import secrets;print(secrets.token_hex(16))')"
D="$(mktemp -d)"
DB_PATH="$D/load.db" python -m campus.db
DB_PATH="$D/load.db" TRACKER_MODE=ok python -m gunicorn -b 127.0.0.1:$PORT -w 2 --threads 4 "campus.app:create_app()" >"$D/server.log" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null; wait $PID 2>/dev/null || true' EXIT
for i in $(seq 1 30); do curl -sf "http://127.0.0.1:$PORT/ready" >/dev/null && break; sleep 0.5; done
BASE_URL="http://127.0.0.1:$PORT" python scripts/load_test.py "$SECS" ${LEVELS:-10 25 50}
echo "--- final row counts in the load database:"
python - <<EOF
import sqlite3; c=sqlite3.connect("$D/load.db")
for t in ("bookings","tickets","audit"): print(t, c.execute("select count(*) from "+t).fetchone()[0])
print("integrity:", c.execute("pragma integrity_check").fetchone()[0])
EOF
