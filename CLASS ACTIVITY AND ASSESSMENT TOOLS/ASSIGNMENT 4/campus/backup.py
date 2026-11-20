"""Verified backup / restore of the SQLite database.
A backup is a consistent copy made with SQLite's online-backup API plus a manifest
(row counts per table, sha256, schema version). A named Docker volume is NOT a backup."""
import hashlib
import json
import os
import sqlite3
import sys
import time

TABLES = ("facilities", "bookings", "tickets", "audit")


def _counts(path):
    c = sqlite3.connect(path)
    try:
        out = {}
        for t in TABLES:
            try:
                out[t] = c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]  # nosec B608
            except sqlite3.OperationalError:
                out[t] = None
        try:
            out["schema_version"] = c.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        except sqlite3.OperationalError:
            out["schema_version"] = 0
        return out
    finally:
        c.close()


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(db_path, dest_dir, label=None):
    os.makedirs(dest_dir, exist_ok=True)
    label = label or time.strftime("%Y%m%dT%H%M%S")
    dest = os.path.join(dest_dir, "campus-%s.db" % label)
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)                       # consistent even while the app is writing (WAL)
    finally:
        dst.close()
        src.close()
    manifest = {"file": os.path.basename(dest), "sha256": _sha(dest), "counts": _counts(dest)}
    with open(dest + ".json", "w") as f:
        json.dump(manifest, f, indent=1)
    return dest, manifest


def verify(backup_path):
    """Integrity + manifest check; returns the manifest or raises."""
    manifest = json.load(open(backup_path + ".json"))
    if _sha(backup_path) != manifest["sha256"]:
        raise RuntimeError("backup checksum mismatch")
    c = sqlite3.connect(backup_path)
    try:
        if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("backup failed integrity_check")
    finally:
        c.close()
    if _counts(backup_path) != manifest["counts"]:
        raise RuntimeError("backup row counts differ from manifest")
    return manifest


def restore(backup_path, db_path):
    """Verify the backup, then replace the live database file atomically."""
    manifest = verify(backup_path)
    tmp = db_path + ".restoring"
    src = sqlite3.connect(backup_path)
    dst = sqlite3.connect(tmp)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    for ext in ("-wal", "-shm"):               # drop stale journal files of the damaged DB
        if os.path.exists(db_path + ext):
            os.remove(db_path + ext)
    os.replace(tmp, db_path)
    if _counts(db_path) != manifest["counts"]:
        raise RuntimeError("restored database differs from manifest")
    return manifest


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "backup":
        print(json.dumps(backup(sys.argv[2], sys.argv[3])[1], indent=1))
    elif cmd == "restore":
        print(json.dumps(restore(sys.argv[2], sys.argv[3]), indent=1))
    elif cmd == "verify":
        print(json.dumps(verify(sys.argv[2]), indent=1))
