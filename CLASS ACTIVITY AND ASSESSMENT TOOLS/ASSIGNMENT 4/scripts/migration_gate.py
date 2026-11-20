"""Pre/post migration evidence: row counts + content fingerprints of the ORIGINAL columns, so a
migration can be proven not to have altered or lost existing records.
  python scripts/migration_gate.py snapshot <db> <snapshot.json>
  python scripts/migration_gate.py verify   <db> <snapshot.json>      (exit 1 on any failure)"""
import hashlib
import json
import sqlite3
import sys

ORIGINAL_COLUMNS = {   # release-1.0 schema columns that must never change
    "facilities": "id,code,name,restricted",
    "bookings": "id,facility_id,requester,title,start_utc,end_utc,status,created_utc",
    "tickets": ("id,title,description,category,impact,urgency,priority,state,version,notes,source,"
                "event_id,facility_id,reporter,created_utc,sla_due_utc,sync_status,remote_id"),
    "audit": "id,ticket_id,booking_id,action,from_state,to_state,actor,role,at_utc",
}


def snapshot(path, max_ids=None):
    """Fingerprint of the rows that existed BEFORE the migration (id <= max_id). Rows a migration
    legitimately adds (e.g. a new reference facility) are not part of the comparison."""
    c = sqlite3.connect(path)
    out = {}
    try:
        for t, cols in ORIGINAL_COLUMNS.items():
            h = hashlib.sha256()
            n = 0
            limit = (max_ids or {}).get(t)
            if limit is None:
                limit = c.execute("SELECT COALESCE(MAX(id),0) FROM %s" % t).fetchone()[0]  # nosec B608
            for row in c.execute("SELECT %s FROM %s WHERE id<=%d ORDER BY id" % (cols, t, limit)):  # nosec B608
                h.update(repr(row).encode())
                n += 1
            out[t] = {"rows": n, "max_id": limit, "sha256": h.hexdigest()}
    finally:
        c.close()
    return out


def verify(path, snap):
    """Returns a list of failure strings (empty = gate passes)."""
    fails = []
    c = sqlite3.connect(path)
    try:
        ver = c.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        if ver != 2:
            fails.append("schema version is %r, expected 2" % ver)
        if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            fails.append("integrity_check failed")
        if c.execute("PRAGMA foreign_key_check").fetchall():
            fails.append("foreign_key_check found orphans")
        for t in ("bookings", "tickets"):
            n = c.execute("SELECT COUNT(*) FROM %s WHERE campus_code IS NULL OR policy_version IS NULL" % t).fetchone()[0]  # nosec B608
            if n:
                fails.append("%d %s rows lack campus_code/policy_version after backfill" % (n, t))
        orphan = c.execute("SELECT COUNT(*) FROM tickets t WHERE sync_status='Pending' AND NOT EXISTS "
                           "(SELECT 1 FROM outbox o WHERE o.kind='issue' AND o.ref_id=t.id)").fetchone()[0]
        if orphan:
            fails.append("%d Pending tickets have no outbox intent" % orphan)
    finally:
        c.close()
    now = snapshot(path, {t: v["max_id"] for t, v in snap.items()})
    for t, before in snap.items():
        if now[t] != before:
            fails.append("%s: original data changed (before %s rows, after %s rows; checksum %s)" % (
                t, before["rows"], now[t]["rows"], "same" if now[t]["sha256"] == before["sha256"] else "DIFFERENT"))
    return fails


if __name__ == "__main__":
    cmd, db, snapfile = sys.argv[1:4]
    if cmd == "snapshot":
        json.dump(snapshot(db), open(snapfile, "w"), indent=1)
        print("snapshot written:", {t: v["rows"] for t, v in json.load(open(snapfile)).items()})
    else:
        f = verify(db, json.load(open(snapfile)))
        print("MIGRATION GATE:", "PASSED" if not f else "FAILED")
        for x in f:
            print("  -", x)
        sys.exit(1 if f else 0)
