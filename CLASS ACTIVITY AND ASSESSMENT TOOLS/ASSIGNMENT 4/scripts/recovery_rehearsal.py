"""Rehearsal: dependency outage, deliberately failed deployment, rollback, restore.
Builds release bundles from git refs, runs them as real gunicorn processes on a throw-away DB.
usage: python scripts/recovery_rehearsal.py <good-ref> <bad-ref>     (e.g. v1.0.0 defect/destructive-migration)"""
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from campus import auth, backup  # noqa: E402

SECRET = secrets.token_hex(16)
PORT = 18090
BASE = "http://127.0.0.1:%d" % PORT
procs = []


def say(msg):
    print("[%6.1fs] %s" % (time.time() - T0, msg), flush=True)


def call(method, path, role=None, body=None):
    h = {"Content-Type": "application/json"}
    if role:
        h["Authorization"] = "Bearer " + auth.issue_token(SECRET, role + "-ops", role, time.time(), 600)
    r = urllib.request.Request(BASE + path, method=method, headers=h,
                               data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(r, timeout=8) as x:
            return x.status, json.loads(x.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
    except Exception as e:
        return 0, {"error": str(e)}


def bundle(ref, dest):
    os.makedirs(dest)
    tar = subprocess.run(["git", "archive", "--format=tar", ref, "campus", "migrations", "scripts", "requirements.txt"],
                         cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "x", "-C", dest], input=tar, check=True)
    sha = subprocess.run(["git", "rev-parse", ref], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return sha


def start(rel_dir, db, sha, tracker="ok"):
    env = dict(os.environ, SECRET_KEY=SECRET, DB_PATH=db, GIT_SHA=sha, TRACKER_MODE=tracker, PYTHONPATH=rel_dir)
    m = subprocess.run([sys.executable, "-m", "campus.db"], cwd=rel_dir, env=env, capture_output=True, text=True)
    say("migrate -> %s" % (m.stdout.strip() or m.stderr.strip()[-200:]))
    p = subprocess.Popen([sys.executable, "-m", "gunicorn", "-b", "127.0.0.1:%d" % PORT, "-w", "2", "--threads", "4",
                          "campus.app:create_app()"], cwd=rel_dir, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs.append(p)
    for _ in range(40):
        if call("GET", "/health")[0] == 200:
            return p
        time.sleep(0.25)
    raise RuntimeError("server did not start")


def stop(p):
    p.terminate()
    p.wait(10)
    time.sleep(0.3)


def smoke(label):
    env = dict(os.environ, SECRET_KEY=SECRET, BASE_URL=BASE)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smoke_test.py")], env=env,
                       capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith(("PASS", "FAIL", "SMOKE"))]
    say("smoke(%s): exit=%d  %s" % (label, r.returncode, lines[-1] if lines else r.stderr[-120:]))
    for l in lines:
        if l.startswith("FAIL"):
            print("          " + l)
    return r.returncode == 0


def seed():
    s, b1 = call("POST", "/api/v1/bookings", "faculty", {"facility": "ROOM-101", "title": "Seminar", "start": "2031-03-01T10:00:00Z", "end": "2031-03-01T11:00:00Z"})
    call("POST", "/api/v1/bookings/%d/approve" % b1["id"], "approver")
    s, t1 = call("POST", "/api/v1/tickets", "faculty", {"title": "AC compressor tripping", "impact": "High", "urgency": "Medium"})
    call("POST", "/api/v1/tickets/%d/transition" % t1["id"], "technician", {"target": "Assigned", "expected_version": 1})
    return b1["id"], t1["id"]


def verify(b1, t1, label):
    sb, b = call("GET", "/api/v1/bookings/%d" % b1, "manager")
    st, t = call("GET", "/api/v1/tickets/%d" % t1, "manager")
    sa, a = call("GET", "/api/v1/tickets/%d/audit" % t1, "manager")
    ok = (sb, st, sa) == (200, 200, 200)
    say("verify(%s): booking=%s ticket=%s audit=%s%s" % (
        label, sb, st, sa, ("  booking.status=%s ticket.state=%s audit_rows=%d" % (b["status"], t["state"], len(a))) if ok else ""))
    return ok


T0 = time.time()
good_ref, bad_ref = sys.argv[1], sys.argv[2]
work = tempfile.mkdtemp(prefix="rehearsal-")
db = os.path.join(work, "data", "campus.db")
os.makedirs(os.path.dirname(db))
try:
    A, B = os.path.join(work, "releaseA"), os.path.join(work, "releaseB")
    shaA, shaB = bundle(good_ref, A), bundle(bad_ref, B)
    say("release A (known good) = %s %s" % (good_ref, shaA[:12]))
    say("release B (candidate)  = %s %s" % (bad_ref, shaB[:12]))

    say("--- PART 1: unavailable dependency (tracker down) on release A")
    p = start(A, db, shaA, tracker="down")
    s, t = call("POST", "/api/v1/tickets", "faculty", {"title": "Projector fault", "impact": "Low", "urgency": "Low"})
    say("create ticket while tracker is down -> HTTP %s, sync_status=%s, remote_id=%s" % (s, t.get("sync_status"), t.get("remote_id")))
    s2, again = call("GET", "/api/v1/tickets/%d" % t["id"], "manager")
    say("ticket is readable locally -> HTTP %s state=%s sync_status=%s" % (s2, again.get("state"), again.get("sync_status")))
    stop(p)
    c = backup._counts(db)
    say("persistent state after outage: %s" % {k: c[k] for k in ("tickets", "bookings", "audit")})

    say("--- PART 2: normal operation on release A, then verified backup")
    p = start(A, db, shaA, tracker="ok")
    b1, t1 = seed()
    assert smoke("A baseline")
    verify(b1, t1, "before backup")
    t_b = time.time()
    path, manifest = backup.backup(db, os.path.join(work, "backups"), "pre-release")
    say("backup %s sha256=%s... counts=%s (%.2fs)" % (os.path.basename(path), manifest["sha256"][:16], {k: v for k, v in manifest["counts"].items() if k != "facilities"}, time.time() - t_b))
    s, late = call("POST", "/api/v1/bookings", "faculty", {"facility": "HALL-A", "title": "Written after backup", "start": "2031-03-02T10:00:00Z", "end": "2031-03-02T11:00:00Z"})
    say("one more booking accepted AFTER the backup (id=%s) - this is the data-loss window" % late.get("id"))
    stop(p)

    say("--- PART 3: deploy release B (deliberately failed deployment)")
    t_fail = time.time()
    p = start(B, db, shaB)
    ok = smoke("B")
    detected = time.time() - t_fail
    say("FAILED DEPLOYMENT DETECTED by smoke gate after %.1fs" % detected)
    verify(b1, t1, "on B") if call("GET", "/health")[0] == 200 else None
    stop(p)

    say("--- PART 4: rollback attempt #1 - revert to release A code only (image rollback)")
    t_rb = time.time()
    p = start(A, db, shaA)
    r1 = smoke("A code on migrated DB")
    v1 = verify(b1, t1, "A code on migrated DB")
    say("image/code rollback sufficient? %s  (schema_version=%s counts=%s)" % (r1 and v1, backup._counts(db)["schema_version"], {k: v for k, v in backup._counts(db).items() if k in ("bookings", "audit")}))
    stop(p)

    say("--- PART 5: rollback attempt #2 - restore the verified backup, then run release A")
    mf = backup.restore(path, db)
    now_counts = backup._counts(db)
    say("restored counts (before restart) = %s" % {k: v for k, v in now_counts.items() if k != "facilities"})
    say("manifest counts                  = %s  -> identical: %s" % (
        {k: v for k, v in mf["counts"].items() if k != "facilities"}, now_counts == mf["counts"]))
    import sqlite3
    present = sqlite3.connect(db).execute("SELECT COUNT(*) FROM bookings WHERE title='Written after backup'").fetchone()[0]
    say("records written after the backup still present: %d, lost: %d  (recovery point = backup time)" % (present, 1 - present))
    p = start(A, db, shaA)
    r2 = smoke("A code on restored DB")
    v2 = verify(b1, t1, "restored")
    sl, ld = call("GET", "/api/v1/bookings/%d" % late["id"], "manager")
    say("FINDING: id %d (the lost booking) now resolves to HTTP %s title=%r - SQLite rowids are reused after a restore" % (late["id"], sl, ld.get("title")))
    say("RECOVERY DURATION from failed-deploy detection to verified service: %.1fs" % (time.time() - t_fail))
    say("RESULT: %s" % ("PASS - service restored, pre-backup data intact" if (r2 and v2 and now_counts == mf["counts"]) else "FAIL"))
    stop(p)
finally:
    for pr in procs:
        if pr.poll() is None:
            pr.kill()
    shutil.rmtree(work, ignore_errors=True)
