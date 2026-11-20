"""Post-deployment smoke journey: readiness + authenticated create-read-transition.
Usage: BASE_URL=http://127.0.0.1:18000 SECRET_KEY=... [EXPECT_COMMIT=sha] [SMOKE_V2=1] python scripts/smoke_test.py
Exit code 0 only if every step passes."""
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from campus import auth  # noqa: E402

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:18000")
SECRET = os.environ["SECRET_KEY"]
EXPECT = os.environ.get("EXPECT_COMMIT")
fails = []


def call(method, path, role=None, body=None):
    hdr = {"Content-Type": "application/json"}
    if role:
        hdr["Authorization"] = "Bearer " + auth.issue_token(SECRET, role + "-smoke", role, time.time(), 300)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" -> " + str(detail) if not ok else ""))
    if not ok:
        fails.append(name)


# wait for readiness (<= 30 s)
for _ in range(30):
    try:
        if call("GET", "/ready")[0] == 200:
            break
    except Exception:
        pass
    time.sleep(1)
code, body = call("GET", "/ready")
check("ready", code == 200, (code, body))
code, body = call("GET", "/version")
print("deployed version:", body)
if EXPECT:
    check("deployed commit matches pipeline commit", body.get("commit") == EXPECT, body)

day = datetime.now(timezone.utc) + timedelta(days=random.randint(3, 3000))
start = day.replace(hour=random.randint(6, 18), minute=0, second=0, microsecond=0)
payload = {"facility": "ROOM-101", "title": "smoke", "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")}
code, b = call("POST", "/api/v1/bookings", "faculty", payload)
check("faculty can create booking", code == 201, (code, b))
bid = b.get("id")
check("student cannot approve (403)", call("POST", "/api/v1/bookings/%s/approve" % bid, "student")[0] == 403)
check("approver can approve", call("POST", "/api/v1/bookings/%s/approve" % bid, "approver")[0] == 200)
check("overlap rejected (409)", call("POST", "/api/v1/bookings", "faculty", payload)[0] == 409)
code, t = call("POST", "/api/v1/tickets", "faculty",
               {"title": "Projector display flicker", "impact": "Medium", "urgency": "Medium"})
check("ticket created with priority M3", code == 201 and t.get("priority") == "M3", (code, t))
code, t2 = call("POST", "/api/v1/tickets/%s/transition" % t.get("id"), "technician",
                {"target": "Assigned", "expected_version": t.get("version")})
check("technician transition", code == 200 and t2.get("state") == "Assigned", (code, t2))
check("no token -> 401", call("GET", "/api/v1/bookings")[0] == 401)

if os.environ.get("SMOKE_V2"):
    code, b2 = call("POST", "/api/v2/bookings", "faculty", {
        "facility": "HALL-A", "campus": "NORTH", "purpose": "smoke v2",
        "start": (start + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ"), "duration_minutes": 90})
    check("v2 booking created with policy version", code == 201 and b2.get("policy_version"), (code, b2))
    code, old = call("GET", "/api/v1/bookings/%s" % bid, "faculty")
    check("old v1 client still reads its booking", code == 200 and old.get("id") == bid, (code, old))

print("SMOKE", "FAILED: %s" % fails if fails else "PASSED")
sys.exit(1 if fails else 0)
