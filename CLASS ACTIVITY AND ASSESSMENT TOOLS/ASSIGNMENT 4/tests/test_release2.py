"""Release 2.0 checks: campus policies, revised API compatibility, durable integration,
and migration preservation. Layer markers are set per test."""
import os
import sqlite3
import sys
from datetime import timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import make_v1_fixture      # noqa: E402
import migration_gate       # noqa: E402

from campus import integration, policy, rules   # noqa: E402
from campus.db import connect, current_version, migrate   # noqa: E402
from conftest import Env, booking              # noqa: E402

POLS = [{"campus_code": "MAIN", "policy_version": 1, "max_minutes": 180, "temp_limit": "28.0"},
        {"campus_code": "MAIN", "policy_version": 2, "max_minutes": 180, "temp_limit": "28.0"},
        {"campus_code": "NORTH", "policy_version": 2, "max_minutes": 120, "temp_limit": "26.5"}]


# ------------------------------------------------------------------------- unit
@pytest.mark.unit
def test_U12_policy_selection_latest_exact_and_default_fallback():
    assert policy.select_policy(POLS, "NORTH")["max_minutes"] == 120
    assert policy.select_policy(POLS, "MAIN")["policy_version"] == 2           # latest
    assert policy.select_policy(POLS, "MAIN", version=1)["policy_version"] == 1  # recorded version
    assert policy.select_policy(POLS, "UNKNOWN")["campus_code"] == "MAIN"      # safe default
    assert policy.select_policy(POLS, None)["campus_code"] == "MAIN"
    with pytest.raises(rules.RuleError):
        policy.select_policy(POLS, "MAIN", version=99)
    with pytest.raises(rules.RuleError):
        policy.select_policy([], "MAIN")


@pytest.mark.unit
@pytest.mark.parametrize("attempts,delay", [(1, 60), (2, 120), (3, 240), (4, 480), (5, None)])
def test_U13_retry_backoff_is_bounded(attempts, delay):
    assert integration.backoff_seconds(attempts) == delay


# ------------------------------------------------------------------ integration
def v2(env, role, **kw):
    body = {"facility": "ROOM-101", "purpose": "Seminar", "start": "2026-11-25T10:00:00Z",
            "duration_minutes": 60}
    body.update(kw)
    return env.client.post("/api/v2/bookings", json=body, headers=env.h(role))


@pytest.mark.integration
@pytest.mark.parametrize("facility,campus,ok,over", [
    ("ROOM-101", "MAIN", 180, 181), ("HALL-A", "NORTH", 120, 121), ("LAB-S1", "SOUTH", 240, 241)])
def test_I9_v2_booking_duration_limit_depends_on_campus(env, facility, campus, ok, over):
    r = v2(env, "faculty", facility=facility, duration_minutes=ok)
    assert r.status_code == 201
    assert (r.get_json()["campus"], r.get_json()["policy_version"], r.get_json()["duration_minutes"]) == (campus, 2, ok)
    rej = v2(env, "faculty", facility=facility, duration_minutes=over, start="2026-12-01T10:00:00Z")
    assert rej.status_code == 400 and ("max %d minutes" % ok) in rej.get_json()["message"]
    assert env.count("bookings") == 1


@pytest.mark.integration
@pytest.mark.parametrize("facility,value,breach", [
    ("ROOM-101", 28.0, False), ("ROOM-101", 28.01, True),
    ("HALL-A", 26.5, False), ("HALL-A", 26.51, True),
    ("LAB-S1", 30.0, False), ("LAB-S1", 30.01, True)])
def test_I10_sensor_threshold_depends_on_campus(env, facility, value, breach):
    r = env.client.post("/api/v1/sensor-events", headers=env.h("sensor"), json={
        "source": "s", "event_id": "e", "facility": facility, "metric": "temperature", "value": value})
    assert r.get_json()["breach"] is breach


@pytest.mark.integration
def test_I11_old_v1_clients_keep_working_and_are_marked_deprecated(env):
    r = env.client.post("/api/v1/bookings", json=booking(), headers=env.h("faculty"))
    assert r.status_code == 201
    assert set(r.get_json()) == {"id", "facility", "requester", "title", "start", "end", "status"}   # unchanged shape
    assert r.headers["Deprecation"] == "true" and "successor-version" in r.headers["Link"]
    bid = r.get_json()["id"]
    new = env.client.get("/api/v2/bookings/%d" % bid, headers=env.h("faculty")).get_json()
    assert (new["campus"], new["policy_version"], new["duration_minutes"]) == ("MAIN", 2, 60)
    created_v2 = v2(env, "faculty", start="2026-11-26T09:00:00Z").get_json()
    assert env.client.get("/api/v1/bookings/%d" % created_v2["id"], headers=env.h("faculty")).status_code == 200


@pytest.mark.integration
def test_I12_calendar_outage_keeps_local_approval_and_retries_on_a_bounded_schedule(env):
    env.calendar.mode = "down"
    b = env.client.post("/api/v1/bookings", json=booking(), headers=env.h("faculty")).get_json()
    a = env.client.post("/api/v2/bookings/%d/approve" % b["id"], headers=env.h("approver")).get_json()
    assert a["status"] == "Approved" and a["calendar_status"] == "Pending"          # not shown as synced
    row = lambda: env.scalar("SELECT attempts||'|'||status||'|'||next_attempt_utc FROM outbox WHERE kind='calendar'")  # noqa: E731
    assert row() == "1|Pending|2026-11-20T08:01:00Z"
    env.clock += timedelta(seconds=30)
    assert integration.flush(connect(env.path), env.clock, {"issue": env.tracker, "calendar": env.calendar})["processed"] == 0
    env.clock += timedelta(seconds=31)                                               # now due, still down
    r = env.client.post("/api/v2/integrations/flush", headers=env.h("technician")).get_json()
    assert r["Pending"] == 1 and row().startswith("2|Pending|2026-11-20T08:03:01Z")
    env.calendar.mode = "ok"
    env.clock += timedelta(seconds=200)
    r = env.client.post("/api/v2/integrations/flush", headers=env.h("technician")).get_json()
    assert r["Synced"] == 1
    again = env.client.post("/api/v2/integrations/flush", headers=env.h("technician")).get_json()
    assert again["processed"] == 0 and len(env.calendar.issues) == 1                 # exactly one remote event
    assert env.client.get("/api/v2/bookings/%d" % b["id"], headers=env.h("manager")).get_json()["calendar_status"] == "Synced"


@pytest.mark.integration
def test_I13_after_five_failures_item_needs_operator_and_local_state_is_intact(env):
    env.tracker.mode = "down"
    t = env.client.post("/api/v1/tickets", headers=env.h("faculty"),
                        json={"title": "Door lock jammed", "impact": "High", "urgency": "High"}).get_json()
    for _ in range(4):
        env.clock += timedelta(hours=1)
        env.client.post("/api/v2/integrations/flush", headers=env.h("technician"))
    st = env.client.get("/api/v2/integrations/status", headers=env.h("technician")).get_json()
    assert st["counts"]["NeedsOperator"] == 1 and st["oldest_unsynced_age_s"] > 0
    got = env.client.get("/api/v1/tickets/%d" % t["id"], headers=env.h("manager")).get_json()
    assert got["state"] == "New" and got["sync_status"] == "Pending"
    env.clock += timedelta(hours=1)
    assert env.client.post("/api/v2/integrations/flush", headers=env.h("technician")).get_json()["processed"] == 0  # bounded: no endless retry
    env.tracker.mode = "ok"                                                           # operator fixes the dependency, then forces a sync
    s = env.client.post("/api/v1/tickets/%d/sync" % t["id"], headers=env.h("technician")).get_json()
    assert s["sync_status"] == "Synced"


@pytest.mark.integration
def test_I14_integration_controls_reject_unauthorised_roles(env):
    for role in ("student", "faculty", "approver"):
        assert env.client.post("/api/v2/integrations/flush", headers=env.h(role)).status_code == 403
        assert env.client.get("/api/v2/integrations/status", headers=env.h(role)).status_code == 403


# ------------------------------------------------------- regression on migrated data
def legacy_env(tmp_path):
    p = str(tmp_path / "legacy.db")
    make_v1_fixture.make(p)             # schema 001 only
    return Env(p)                       # Env migrates -> applies 002 (expand)


@pytest.mark.regression
def test_R9_legacy_records_keep_their_recorded_policy_new_records_use_campus_policy(tmp_path):
    env = legacy_env(tmp_path)
    long_hall = env.scalar("SELECT b.id FROM bookings b WHERE b.facility_id=3 AND "
                           "(julianday(end_utc)-julianday(start_utc))*1440 > 150 LIMIT 1")
    assert long_hall, "fixture must contain a 180-minute HALL-A booking (legal under release 1.0)"
    old = env.client.get("/api/v2/bookings/%d" % long_hall, headers=env.h("manager")).get_json()
    assert (old["policy_version"], old["campus"], old["duration_minutes"]) == (1, "MAIN", 180)
    assert env.client.get("/api/v1/bookings/%d" % long_hall, headers=env.h("manager")).status_code == 200
    new = env.client.post("/api/v1/bookings", headers=env.h("faculty"), json=booking(
        facility="HALL-A", start="2027-05-01T10:00:00Z", end="2027-05-01T13:00:00Z"))
    assert new.status_code == 400                                   # 180 min now exceeds NORTH's 120


@pytest.mark.regression
def test_R10_legacy_tickets_and_audit_history_remain_accessible(tmp_path):
    env = legacy_env(tmp_path)
    t = env.client.get("/api/v1/tickets/1", headers=env.h("manager"))
    a = env.client.get("/api/v1/tickets/1/audit", headers=env.h("manager"))
    assert t.status_code == 200 and a.status_code == 200 and len(a.get_json()) >= 1
    assert env.count("audit") == 320 and env.count("tickets") == 120 and env.count("bookings") == 200


# ---------------------------------------------------------------------- migration
@pytest.mark.migration
def test_M6_migration_preserves_every_existing_record_and_is_idempotent(tmp_path):
    p = str(tmp_path / "fx.db")
    make_v1_fixture.make(p)
    snap = migration_gate.snapshot(p)
    assert snap["bookings"]["rows"] == 200 and snap["tickets"]["rows"] == 120
    assert migrate(p) == [2]
    assert migration_gate.verify(p, snap) == []
    assert migrate(p) == []
    n_pending = sqlite3.connect(p).execute("SELECT COUNT(*) FROM tickets WHERE sync_status='Pending'").fetchone()[0]
    assert sqlite3.connect(p).execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == n_pending > 0


@pytest.mark.migration
def test_M7_failed_expand_migration_leaves_release1_data_and_schema_untouched(tmp_path):
    p = str(tmp_path / "fx.db")
    make_v1_fixture.make(p)
    before = migration_gate.snapshot(p)
    with pytest.raises(RuntimeError):
        migrate(p, fail_after=2)
    assert current_version(connect(p)) == 1
    assert migration_gate.snapshot(p) == before
    cols = [r[1] for r in sqlite3.connect(p).execute("PRAGMA table_info(bookings)")]
    assert "policy_version" not in cols                              # DDL rolled back too
    assert migrate(p) == [2]                                          # and the retry succeeds


@pytest.mark.migration
def test_M8_gate_negative_control_detects_loss_and_unfilled_backfill(tmp_path):
    p = str(tmp_path / "fx.db")
    make_v1_fixture.make(p)
    snap = migration_gate.snapshot(p)
    migrate(p)
    c = sqlite3.connect(p)
    c.execute("DELETE FROM bookings WHERE id=5")
    c.execute("UPDATE tickets SET policy_version=NULL WHERE id=7")
    c.commit()
    msgs = " | ".join(migration_gate.verify(p, snap))
    assert "bookings: original data changed" in msgs and "lack campus_code/policy_version" in msgs


@pytest.mark.migration
def test_M9_release1_style_inserts_still_work_on_the_expanded_schema(tmp_path):
    p = str(tmp_path / "fx.db")
    migrate(p)
    c = sqlite3.connect(p)
    c.execute("INSERT INTO bookings(facility_id,requester,title,start_utc,end_utc,created_utc) "
              "VALUES(1,'old','t','2027-01-01T10:00:00Z','2027-01-01T11:00:00Z','2026-11-20T00:00:00Z')")
    c.execute("INSERT INTO tickets(title,category,impact,urgency,priority,state,reporter,created_utc,sla_due_utc) "
              "VALUES('t','HVAC','High','High','M1','New','old','2026-11-20T00:00:00Z','2026-11-20T04:00:00Z')")
    c.commit()
    assert c.execute("SELECT calendar_status FROM bookings").fetchone()[0] == "NotRequired"
