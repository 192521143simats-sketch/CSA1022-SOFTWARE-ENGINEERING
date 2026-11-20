"""INTEGRATION tests: real Flask app + real services + real SQLite *file* database
(fresh per test) + controlled tracker adapter. Nothing in the app is mocked."""
import threading

import pytest

from conftest import booking

pytestmark = pytest.mark.integration

TICKET = {"title": "AC compressor tripping in Lab 204", "impact": "High", "urgency": "Medium",
          "facility": "ROOM-101"}


def test_I1_full_lifecycle_persists_across_restart_with_audit(env):
    r = env.client.post("/api/v1/tickets", json=TICKET, headers=env.h("faculty"))
    assert r.status_code == 201
    t = r.get_json()
    assert (t["priority"], t["category"], t["state"]) == ("M2", "HVAC", "New")
    v = t["version"]
    for target, notes in [("Assigned", None), ("In Progress", None),
                          ("Resolved", "Reset breaker"), ("Closed", None)]:
        r = env.client.post("/api/v1/tickets/%d/transition" % t["id"],
                            json={"target": target, "expected_version": v, "notes": notes},
                            headers=env.h("technician"))
        assert r.status_code == 200, r.get_json()
        v = r.get_json()["version"]
    env.restart()                                                    # new process, same file
    got = env.client.get("/api/v1/tickets/%d" % t["id"], headers=env.h("manager")).get_json()
    assert (got["state"], got["version"]) == ("Closed", 5)
    audit = env.client.get("/api/v1/tickets/%d/audit" % t["id"], headers=env.h("manager")).get_json()
    states = [a["to_state"] for a in audit if a["action"] != "ticket.sync"]
    assert states == ["New", "Assigned", "In Progress", "Resolved", "Closed"]
    assert [a["action"] for a in audit].count("ticket.sync") == 1   # tracker sync is audited too


def test_I2_repeated_sensor_event_creates_one_ticket(env):
    ev = {"source": "sensor-7", "event_id": "evt-1", "facility": "LAB-204",
          "metric": "temperature", "value": 31.2}
    codes, ids = [], set()
    for _ in range(5):
        r = env.client.post("/api/v1/sensor-events", json=ev, headers=env.h("sensor"))
        codes.append(r.status_code)
        ids.add(r.get_json()["ticket_id"])
    assert codes == [201, 200, 200, 200, 200]
    assert len(ids) == 1 and env.count("tickets") == 1
    t = env.client.get("/api/v1/tickets/%d" % ids.pop(), headers=env.h("technician")).get_json()
    assert (t["priority"], t["category"]) == ("M1", "HVAC")        # restricted lab -> High/High
    assert len(env.tracker.issues) == 1                             # one remote issue as well


def test_I3_student_cannot_approve_and_state_is_unchanged(env):
    b = env.client.post("/api/v1/bookings", json=booking(), headers=env.h("faculty")).get_json()
    audits = env.count("audit")
    r = env.client.post("/api/v1/bookings/%d/approve" % b["id"], headers=env.h("student"))
    assert r.status_code == 403
    assert env.scalar("SELECT status FROM bookings WHERE id=?", b["id"]) == "Pending"
    assert env.count("audit") == audits                             # no approval audit row


def test_I4_overlap_rejected_adjacent_accepted_and_approved_still_blocks(env):
    f = env.h("faculty")
    first = env.client.post("/api/v1/bookings", json=booking(), headers=f).get_json()
    over = env.client.post("/api/v1/bookings", headers=f,
                           json=booking(start="2026-11-21T10:30:00Z", end="2026-11-21T11:30:00Z"))
    assert over.status_code == 409
    adj = env.client.post("/api/v1/bookings", headers=f,
                          json=booking(start="2026-11-21T11:00:00Z", end="2026-11-21T12:00:00Z"))
    assert adj.status_code == 201
    env.client.post("/api/v1/bookings/%d/approve" % first["id"], headers=env.h("approver"))
    still = env.client.post("/api/v1/bookings", headers=f,
                            json=booking(start="2026-11-21T10:15:00Z", end="2026-11-21T10:45:00Z"))
    assert still.status_code == 409                                  # Approved bookings block too
    assert env.count("bookings") == 2


def test_I5_concurrent_requests_for_one_slot_accept_exactly_one(env):
    results = []

    def go(i):
        c = env.app.test_client()
        r = c.post("/api/v1/bookings", json=booking(title="T%d" % i), headers=env.h("faculty", "f%d" % i))
        results.append(r.status_code)

    threads = [threading.Thread(target=go, args=(i,)) for i in range(10)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(results) == [201] + [409] * 9
    assert env.count("bookings") == 1


def test_I6_tracker_outage_keeps_local_work_pending_then_sync_without_duplicates(env):
    env.tracker.mode = "down"
    r = env.client.post("/api/v1/tickets", json=TICKET, headers=env.h("faculty"))
    t = r.get_json()
    assert r.status_code == 201 and t["sync_status"] == "Pending" and t["remote_id"] is None
    assert env.count("tickets") == 1
    env.tracker.mode = "timeout-after-create"          # remote created, reply lost
    s = env.client.post("/api/v1/tickets/%d/sync" % t["id"], headers=env.h("technician")).get_json()
    assert s["sync_status"] == "Pending"               # NOT shown as synced without a remote id
    env.tracker.mode = "ok"
    s = env.client.post("/api/v1/tickets/%d/sync" % t["id"], headers=env.h("technician")).get_json()
    assert s["sync_status"] == "Synced" and s["remote_id"] == "REMOTE-1"
    assert len(env.tracker.issues) == 1                # idempotency key prevented a duplicate


@pytest.mark.parametrize("payload", [
    {"impact": "High", "urgency": "High"},                         # no title
    {"title": "  ", "impact": "High", "urgency": "High"},
    {"title": "x", "impact": "Severe", "urgency": "High"},
    {"title": "x", "impact": "High"},                              # no urgency
])
def test_I7_missing_or_invalid_ticket_details_write_nothing(env, payload):
    r = env.client.post("/api/v1/tickets", json=payload, headers=env.h("faculty"))
    assert r.status_code == 400
    assert env.count("tickets") == 0 and env.count("audit") == 0


def test_I8_restricted_lab_approval_needs_manager_or_admin(env):
    b = env.client.post("/api/v1/bookings", json=booking(facility="LAB-204"), headers=env.h("faculty")).get_json()
    assert env.client.post("/api/v1/bookings/%d/approve" % b["id"], headers=env.h("approver")).status_code == 403
    assert env.scalar("SELECT status FROM bookings WHERE id=?", b["id"]) == "Pending"
    assert env.client.post("/api/v1/bookings/%d/approve" % b["id"], headers=env.h("manager")).status_code == 200
    assert env.scalar("SELECT status FROM bookings WHERE id=?", b["id"]) == "Approved"
