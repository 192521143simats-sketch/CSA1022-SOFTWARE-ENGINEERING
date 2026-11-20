"""Q6 rehearsal on SYNTHETIC release-1.0 data: backup -> migrate -> gate; then a deliberately
unsafe migration is caught by the gate and recovered from the verified backup.
usage: python scripts/migration_rehearsal.py"""
import os, shutil, sqlite3, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import make_v1_fixture, migration_gate  # noqa
from campus import backup  # noqa
from campus.db import connect, current_version, migrate  # noqa

d = tempfile.mkdtemp(prefix="migr-"); db = os.path.join(d, "campus.db")
make_v1_fixture.make(db)
snap = migration_gate.snapshot(db)
print("1. release-1.0 data:", {t: v["rows"] for t, v in snap.items()}, "schema", current_version(connect(db)))
b, m = backup.backup(db, os.path.join(d, "bk"), "pre-2.0"); print("2. verified backup:", m["sha256"][:16], m["counts"])

print("3. migration 002 with injected failure (rehearse failed migration)")
try: migrate(db, fail_after=2)
except RuntimeError as e: print("   failed as designed:", e)
print("   after failure: schema", current_version(connect(db)), "| data unchanged:", migration_gate.snapshot(db) == snap)

print("4. real migration 002:", migrate(db)); f = migration_gate.verify(db, snap)
print("   MIGRATION GATE:", "PASSED" if not f else f)
c = sqlite3.connect(db)
print("   backfill: policy_version=1 rows:", c.execute("select count(*) from bookings where policy_version=1").fetchone()[0],
      "| outbox intents for Pending tickets:", c.execute("select count(*) from outbox").fetchone()[0]); c.close()

print("5. UNSAFE migration 003 (deliberate): backfill that overwrites existing booking titles + drops audit rows")
c = sqlite3.connect(db); c.execute("UPDATE bookings SET title='' WHERE id<=10"); c.execute("DELETE FROM audit WHERE id<=5"); c.commit(); c.close()
f = migration_gate.verify(db, snap); print("   MIGRATION GATE:", "PASSED" if not f else "FAILED (blocks release)")
for x in f: print("    -", x)
print("6. recovery: restore verified backup, then re-run the safe migration")
backup.restore(b, db); print("   restored schema", current_version(connect(db)), "| data identical to pre-migration:", migration_gate.snapshot(db) == snap)
migrate(db); f = migration_gate.verify(db, snap); print("   re-migrated; MIGRATION GATE:", "PASSED" if not f else f)
shutil.rmtree(d)
sys.exit(0 if not f else 1)
