"""Bounded load experiment (stdlib only). Reports ACTUAL workload and observed behaviour.
usage: BASE_URL=... SECRET_KEY=... python scripts/load_test.py [seconds-per-level] [levels...]
Each virtual client loops: create booking -> read booking -> create ticket -> read ticket,
opening a new HTTP connection per request (no keep-alive), so figures are conservative."""
import json
import os
import platform
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from campus import auth  # noqa: E402

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:18082")
SECRET = os.environ["SECRET_KEY"]


def req(method, path, role, body=None):
    tok = auth.issue_token(SECRET, role + "-load", role, time.time(), 600)
    r = urllib.request.Request(BASE + path, method=method,
                               data=json.dumps(body).encode() if body is not None else None,
                               headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            code, data = resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        code, data = e.code, {}
    except Exception:
        code, data = 0, {}
    return code, data, (time.perf_counter() - t0) * 1000


def level(clients, seconds, slot_base=0):
    lat, codes, stop = [], {}, time.time() + seconds
    lock = threading.Lock()

    def worker(cid):
        i = 0
        while time.time() < stop:
            day = datetime(2031, 1, 1, tzinfo=timezone.utc) + timedelta(days=slot_base + cid * 5000 + i)   # unique slot per level/client/iteration
            body = {"facility": "HALL-A", "title": "load", "start": day.strftime("%Y-%m-%dT10:00:00Z"),
                    "end": day.strftime("%Y-%m-%dT11:00:00Z")}
            steps = [("POST", "/api/v1/bookings", "faculty", body),
                     ("POST", "/api/v1/tickets", "faculty",
                      {"title": "Projector display flicker", "impact": "Low", "urgency": "Low"})]
            made = []
            for m, p, r, b in steps:
                c, d, ms = req(m, p, r, b)
                made.append(d.get("id"))
                with lock:
                    lat.append(ms)
                    codes[c] = codes.get(c, 0) + 1
            for path, role, key in (("/api/v1/bookings/%s", "faculty", 0), ("/api/v1/tickets/%s", "faculty", 1)):
                c, d, ms = req("GET", path % made[key], role)
                with lock:
                    lat.append(ms)
                    codes[c] = codes.get(c, 0) + 1
            i += 1

    t0 = time.time()
    th = [threading.Thread(target=worker, args=(c,)) for c in range(clients)]
    [t.start() for t in th]
    [t.join() for t in th]
    wall = time.time() - t0
    lat.sort()
    n = len(lat)
    ok = sum(v for k, v in codes.items() if k in (200, 201))
    return {"clients": clients, "duration_s": round(wall, 1), "requests": n, "ok": ok, "errors": n - ok,
            "status_codes": codes, "throughput_rps": round(n / wall, 1),
            "p50_ms": round(statistics.median(lat), 1), "p95_ms": round(lat[int(0.95 * (n - 1))], 1),
            "max_ms": round(lat[-1], 1)}


def replay_burst(unique=20, repeats=10, clients=32):
    """Same sensor events delivered repeatedly and concurrently: must yield `unique` tickets."""
    jobs = [("evt-%d" % (e % unique)) for e in range(unique * repeats)]
    results, lock = [], threading.Lock()

    def worker():
        while True:
            with lock:
                if not jobs:
                    return
                ev = jobs.pop()
            c, d, ms = req("POST", "/api/v1/sensor-events", "sensor",
                           {"source": "burst-1", "event_id": ev, "facility": "LAB-204",
                            "metric": "temperature", "value": 31.0})
            with lock:
                results.append((c, d.get("ticket_id"), d.get("duplicate"), ms))

    t0 = time.time()
    th = [threading.Thread(target=worker) for _ in range(clients)]
    [t.start() for t in th]
    [t.join() for t in th]
    ids = {r[1] for r in results if r[1]}
    return {"posted": len(results), "created_201": sum(1 for r in results if r[0] == 201),
            "duplicates_200": sum(1 for r in results if r[0] == 200),
            "other": sum(1 for r in results if r[0] not in (200, 201)),
            "distinct_tickets": len(ids), "expected_distinct": unique,
            "wall_s": round(time.time() - t0, 2), "max_ms": round(max(r[3] for r in results), 1)}


if __name__ == "__main__":
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    levels = [int(x) for x in sys.argv[2:]] or [10, 25, 50]
    out = {"environment": {"python": platform.python_version(), "platform": platform.platform(),
                           "cpus": os.cpu_count(), "server": "gunicorn 2 workers x 4 threads, SQLite WAL",
                           "client": "stdlib threads, new connection per request, same host"},
           "levels": [level(c, secs, slot_base=n * 400000) for n, c in enumerate(levels)], "replay": replay_burst()}
    print(json.dumps(out, indent=1))
