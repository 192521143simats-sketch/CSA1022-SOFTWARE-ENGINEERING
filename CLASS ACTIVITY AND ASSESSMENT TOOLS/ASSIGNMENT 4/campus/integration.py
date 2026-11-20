"""Durable-intent integration (release 2.0).
An outbox row is written in the SAME transaction as the business change, so a remote outage can
never lose the intent. Delivery is retried on a bounded schedule; after MAX_ATTEMPTS the item is
flagged for an operator. A record is marked Synced ONLY after the remote returns an identity."""
from datetime import timedelta

from . import rules
from .db import tx
from .tracker import TrackerError

BACKOFF_SECONDS = [60, 120, 240, 480, 960]     # planning assumption: 1,2,4,8,16 minutes
MAX_ATTEMPTS = len(BACKOFF_SECONDS)


def backoff_seconds(attempts):
    """Delay before the next attempt after `attempts` failures; None = give up (operator)."""
    if attempts >= MAX_ATTEMPTS:
        return None
    return BACKOFF_SECONDS[max(attempts, 1) - 1]


def enqueue(db, now, kind, ref_id):
    """Call inside the caller's transaction."""
    db.execute("INSERT OR IGNORE INTO outbox(kind,ref_id,idempotency_key,status,attempts,next_attempt_utc,created_utc)"
               " VALUES(?,?,?, 'Pending',0,?,?)",
               (kind, ref_id, "%s-%d" % (kind, ref_id), rules.fmt_utc(now), rules.fmt_utc(now)))


def _payload(db, row):
    if row["kind"] == "issue":
        t = db.execute("SELECT title FROM tickets WHERE id=?", (row["ref_id"],)).fetchone()
        return {"title": t["title"]}
    b = db.execute("SELECT title,start_utc,end_utc FROM bookings WHERE id=?", (row["ref_id"],)).fetchone()
    return {"title": b["title"], "start": b["start_utc"], "end": b["end_utc"]}


def attempt(db, now, adapters, row):
    """One delivery attempt. Returns 'Synced' | 'Pending' | 'NeedsOperator'."""
    try:
        remote = adapters[row["kind"]].send(row["idempotency_key"], _payload(db, row))
    except TrackerError as exc:
        attempts = row["attempts"] + 1
        delay = backoff_seconds(attempts)
        status = "NeedsOperator" if delay is None else "Pending"
        nxt = rules.fmt_utc(now + timedelta(seconds=delay or 0))
        with tx(db):
            db.execute("UPDATE outbox SET attempts=?, status=?, next_attempt_utc=?, last_error=? WHERE id=?",
                       (attempts, status, nxt, str(exc)[:200], row["id"]))
        return status
    with tx(db):
        db.execute("UPDATE outbox SET status='Synced', remote_id=?, last_error=NULL WHERE id=?",
                   (remote, row["id"]))
        if row["kind"] == "issue":
            db.execute("UPDATE tickets SET sync_status='Synced', remote_id=? WHERE id=?", (remote, row["ref_id"]))
        else:
            db.execute("UPDATE bookings SET calendar_status='Synced' WHERE id=?", (row["ref_id"],))
        db.execute("INSERT INTO audit(ticket_id,booking_id,action,actor,role,at_utc) VALUES(?,?,?,?,?,?)",
                   (row["ref_id"] if row["kind"] == "issue" else None,
                    row["ref_id"] if row["kind"] == "calendar" else None,
                    "ticket.sync" if row["kind"] == "issue" else "booking.calendar_sync",
                    "system", "system", rules.fmt_utc(now)))
    return "Synced"


def attempt_for(db, now, adapters, kind, ref_id, force=False):
    row = db.execute("SELECT * FROM outbox WHERE kind=? AND ref_id=?", (kind, ref_id)).fetchone()
    if row is None or row["status"] == "Synced":
        return "Synced" if row else None
    if not force and row["next_attempt_utc"] > rules.fmt_utc(now):
        return row["status"]
    return attempt(db, now, adapters, row)


def flush(db, now, adapters, limit=50):
    """Process due items, oldest first, at most `limit` (bounded work per call)."""
    rows = db.execute("SELECT * FROM outbox WHERE status='Pending' AND next_attempt_utc<=? ORDER BY id LIMIT ?",
                      (rules.fmt_utc(now), limit)).fetchall()
    out = {"processed": 0, "Synced": 0, "Pending": 0, "NeedsOperator": 0}
    for r in rows:
        out["processed"] += 1
        out[attempt(db, now, adapters, r)] += 1
    return out


def status(db, now):
    counts = {s: 0 for s in ("Pending", "Synced", "NeedsOperator")}
    for r in db.execute("SELECT status, COUNT(*) c FROM outbox GROUP BY status"):
        counts[r["status"]] = r["c"]
    oldest = db.execute("SELECT MIN(created_utc) m FROM outbox WHERE status!='Synced'").fetchone()["m"]
    age = None if oldest is None else int((now - rules.parse_utc(oldest)).total_seconds())
    return {"counts": counts, "oldest_unsynced_age_s": age}
