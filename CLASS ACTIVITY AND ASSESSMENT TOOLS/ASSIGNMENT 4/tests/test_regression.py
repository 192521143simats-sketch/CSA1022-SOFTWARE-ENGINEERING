"""REGRESSION tests: protect behaviour that was correct in earlier releases.
They deliberately overlap the unit/integration layers (same rules, reached through the
public API) so a change to rules, storage or the HTTP contract cannot silently break them."""
import pytest

from conftest import booking

pytestmark = pytest.mark.regression


def _ticket(env, **kw):
    body = {"title": "Door lock jammed", "impact": "High", "urgency": "Medium"}
    body.update(kw)
    return env.client.post("/api/v1/tickets", json=body, headers=env.h("faculty")).get_json()


def test_R1_high_impact_medium_urgency_is_M2_via_api(env):
    assert _ticket(env)["priority"] == "M2"


def test_R2_unknown_terminology_goes_to_manual_review(env):
    assert _ticket(env, title="strange noise somewhere")["category"] == "Manual Review"


def test_R3_resolution_without_notes_is_rejected_and_state_retained(env):
    t = _ticket(env)
    v = t["version"]
    for target in ("Assigned", "In Progress"):
        v = env.client.post("/api/v1/tickets/%d/transition" % t["id"], headers=env.h("technician"),
                            json={"target": target, "expected_version": v}).get_json()["version"]
    r = env.client.post("/api/v1/tickets/%d/transition" % t["id"], headers=env.h("technician"),
                        json={"target": "Resolved", "expected_version": v, "notes": "  "})
    assert r.status_code == 400
    assert env.scalar("SELECT state FROM tickets WHERE id=?", t["id"]) == "In Progress"


def test_R4_stale_version_rejected_and_accepted_state_retained(env):
    t = _ticket(env)
    h = env.h("technician")
    env.client.post("/api/v1/tickets/%d/transition" % t["id"], headers=h,
                    json={"target": "Assigned", "expected_version": 1})
    r = env.client.post("/api/v1/tickets/%d/transition" % t["id"], headers=h,
                        json={"target": "In Progress", "expected_version": 1})
    assert r.status_code == 409
    assert env.scalar("SELECT state||version FROM tickets WHERE id=?", t["id"]) == "Assigned2"


def test_R5_back_to_back_booking_boundary_stays_allowed(env):
    h = env.h("faculty")
    assert env.client.post("/api/v1/bookings", json=booking(), headers=h).status_code == 201
    nxt = booking(start="2026-11-21T11:00:00Z", end="2026-11-21T12:00:00Z")
    assert env.client.post("/api/v1/bookings", json=nxt, headers=h).status_code == 201


def test_R6_duration_limit_180_ok_181_rejected_via_api(env):
    h = env.h("faculty")
    ok = booking(start="2026-11-21T09:00:00Z", end="2026-11-21T12:00:00Z")
    too = booking(facility="HALL-A", start="2026-11-21T09:00:00Z", end="2026-11-21T12:01:00Z")
    assert env.client.post("/api/v1/bookings", json=ok, headers=h).status_code == 201
    assert env.client.post("/api/v1/bookings", json=too, headers=h).status_code == 400


def test_R7_sensor_equality_does_not_breach_but_28_01_does(env):
    h = env.h("sensor")
    base = {"source": "s", "facility": "ROOM-101", "metric": "temperature"}
    eq = env.client.post("/api/v1/sensor-events", json=dict(base, event_id="a", value=28.0), headers=h)
    hi = env.client.post("/api/v1/sensor-events", json=dict(base, event_id="b", value=28.01), headers=h)
    assert eq.get_json()["breach"] is False and hi.get_json()["breach"] is True
    assert env.count("tickets") == 1


def test_R8_records_and_audit_survive_restart(env):
    t = _ticket(env)
    b = env.client.post("/api/v1/bookings", json=booking(), headers=env.h("faculty")).get_json()
    before = (env.count("tickets"), env.count("bookings"), env.count("audit"))
    env.restart()
    assert (env.count("tickets"), env.count("bookings"), env.count("audit")) == before
    assert env.client.get("/api/v1/bookings/%d" % b["id"], headers=env.h("faculty")).status_code == 200
    assert env.client.get("/api/v1/tickets/%d" % t["id"], headers=env.h("manager")).status_code == 200
