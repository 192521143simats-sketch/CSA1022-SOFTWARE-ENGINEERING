"""SQLite access and a small, ordered, transactional migration runner."""
import glob
import os
import re
import sqlite3
from contextlib import contextmanager

MIGRATIONS_DIR = os.environ.get(
    "MIGRATIONS_DIR", os.path.join(os.path.dirname(__file__), "..", "migrations"))


def connect(path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None)  # explicit tx control
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=10000")
    if path != ":memory:":
        db.execute("PRAGMA journal_mode=WAL")
    return db


@contextmanager
def tx(db):
    """BEGIN IMMEDIATE takes the write lock up-front, so check-then-insert
    sequences (booking overlap) cannot interleave across connections."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    else:
        db.execute("COMMIT")


def migration_files(max_version=None):
    files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "[0-9][0-9][0-9]_*.sql")))
    out = []
    for f in files:
        v = int(os.path.basename(f)[:3])
        if max_version is None or v <= max_version:
            out.append((v, f))
    return out


def current_version(db):
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations("
               "version INTEGER PRIMARY KEY, name TEXT, applied_utc TEXT)")
    row = db.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
    return row[0] or 0


def migrate(path, max_version=None, fail_after=None):
    """Apply pending migrations; each file runs in ONE transaction (SQLite DDL is
    transactional), so a failure leaves the previous schema and data untouched.
    `fail_after` (a version number) is a test hook that raises after that file's SQL
    but before COMMIT, to rehearse a failed migration."""
    db = connect(path)
    applied = []
    try:
        cur = current_version(db)
        for v, f in migration_files(max_version):
            if v <= cur:
                continue
            sql = open(f, encoding="utf-8").read()
            statements = [s.strip() for s in re.split(r";\s*(?:\n|$)", sql) if s.strip()]
            db.execute("BEGIN IMMEDIATE")
            try:
                for s in statements:
                    db.execute(s)
                if fail_after == v:
                    raise RuntimeError("injected failure after migration %03d" % v)
                db.execute("INSERT INTO schema_migrations VALUES(?,?,datetime('now'))",
                           (v, os.path.basename(f)))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
            applied.append(v)
    finally:
        db.close()
    return applied


if __name__ == "__main__":
    import sys
    p = os.environ.get("DB_PATH", "campus.db")
    mv = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print("applied:", migrate(p, mv))
