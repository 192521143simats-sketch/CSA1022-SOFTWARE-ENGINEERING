"""MIGRATION + RECOVERY tests (release 1.0 baseline)."""
import sqlite3

import pytest

from campus import backup
from campus.db import connect, current_version, migrate

pytestmark = pytest.mark.migration


def tables(path):
    c = sqlite3.connect(path)
    try:
        return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        c.close()


def test_M1_fresh_database_migrates_and_is_idempotent(tmp_path):
    p = str(tmp_path / "m.db")
    assert migrate(p) == [1, 2]
    assert {"facilities", "bookings", "tickets", "audit", "schema_migrations"} <= tables(p)
    assert migrate(p) == []                                  # second run applies nothing


def test_M2_failed_migration_rolls_back_completely(tmp_path):
    p = str(tmp_path / "m.db")
    with pytest.raises(RuntimeError):
        migrate(p, fail_after=1)
    assert "bookings" not in tables(p)                       # nothing half-applied
    c = connect(p)
    assert current_version(c) == 0
    assert migrate(p) == [1, 2]                              # and it can be retried cleanly


def test_M3_foreign_keys_are_enforced(tmp_path):
    p = str(tmp_path / "m.db")
    migrate(p)
    c = connect(p)
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO bookings(facility_id,requester,title,start_utc,end_utc,created_utc)"
                  " VALUES(999,'x','t','a','b','c')")


def test_M4_backup_verify_restore_round_trip_after_data_loss(tmp_path):
    p = str(tmp_path / "live.db")
    migrate(p)
    c = connect(p)
    c.execute("INSERT INTO bookings(facility_id,requester,title,start_utc,end_utc,created_utc)"
              " VALUES(1,'f1','Study','2026-11-21T10:00:00Z','2026-11-21T11:00:00Z','2026-11-20T08:00:00Z')")
    c.close()
    b, manifest = backup.backup(p, str(tmp_path / "bk"), "t1")
    assert manifest["counts"]["bookings"] == 1
    c = connect(p)
    c.execute("DELETE FROM bookings")                         # simulated destructive incident
    c.close()
    backup.restore(b, p)
    assert backup._counts(p)["bookings"] == 1


def test_M5_corrupted_backup_is_refused(tmp_path):
    p = str(tmp_path / "live.db")
    migrate(p)
    b, _ = backup.backup(p, str(tmp_path / "bk"), "t2")
    with open(b, "ab") as f:
        f.write(b"garbage")
    with pytest.raises(RuntimeError):
        backup.restore(b, p)
