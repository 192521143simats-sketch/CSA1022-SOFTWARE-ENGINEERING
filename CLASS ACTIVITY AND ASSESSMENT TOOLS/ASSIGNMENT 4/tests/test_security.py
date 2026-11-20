"""SECURITY / authorisation tests, performed against the HTTP API directly
(independent of any interface control)."""
import pytest

from conftest import booking

pytestmark = pytest.mark.security

ROLE_MATRIX = [  # (role, endpoint-kind, expected status)
    ("student", "approve", 403), ("faculty", "approve", 403), ("technician", "approve", 403),
    ("sensor", "approve", 403), ("approver", "approve", 200), ("manager", "approve", 200),
    ("admin", "approve", 200),
]


@pytest.mark.parametrize("role,kind,expected", ROLE_MATRIX)
def test_S1_booking_approval_role_matrix(env, role, kind, expected):
    b = env.client.post("/api/v1/bookings", json=booking(), headers=env.h("faculty")).get_json()
    r = env.client.post("/api/v1/bookings/%d/approve" % b["id"], headers=env.h(role))
    assert r.status_code == expected


def test_S2_student_cannot_impersonate_by_claiming_a_role_in_body_or_headers(env):
    b = env.client.post("/api/v1/bookings", json=booking(), headers=env.h("faculty")).get_json()
    h = env.h("student")
    h["X-Role"] = "admin"
    h["X-User"] = "root"
    r = env.client.post("/api/v1/bookings/%d/approve?role=admin" % b["id"],
                        json={"role": "approver", "user": "root"}, headers=h)
    assert r.status_code == 403
    assert env.scalar("SELECT status FROM bookings WHERE id=?", b["id"]) == "Pending"


@pytest.mark.parametrize("hdr", [{}, {"Authorization": "Bearer abc.def"}, {"Authorization": "Basic xyz"}])
def test_S3_missing_or_malformed_credentials_get_401(env, hdr):
    assert env.client.get("/api/v1/bookings", headers=hdr).status_code == 401


def test_S4_expired_and_tampered_tokens_get_401(env):
    expired = env.h("manager", ttl=-1)
    assert env.client.get("/api/v1/bookings", headers=expired).status_code == 401
    good = env.h("student")["Authorization"]
    forged = {"Authorization": good[:-3] + "000"}
    assert env.client.get("/api/v1/bookings", headers=forged).status_code == 401


def test_S5_student_cannot_read_restricted_facility_data_or_others_bookings(env):
    b = env.client.post("/api/v1/bookings", json=booking(facility="LAB-204"), headers=env.h("faculty")).get_json()
    s = env.h("student")
    assert env.client.get("/api/v1/bookings/%d" % b["id"], headers=s).status_code == 403
    assert env.client.get("/api/v1/bookings?facility=LAB-204", headers=s).get_json() == []
    assert env.client.post("/api/v1/bookings", json=booking(facility="LAB-204", start="2026-11-22T10:00:00Z",
                           end="2026-11-22T11:00:00Z"), headers=s).status_code == 403


def test_S6_student_cannot_read_restricted_ticket_transition_or_audit(env):
    t = env.client.post("/api/v1/tickets", headers=env.h("faculty"), json={
        "title": "Fume hood alarm", "impact": "High", "urgency": "High", "facility": "LAB-204"}).get_json()
    s = env.h("student")
    assert env.client.get("/api/v1/tickets/%d" % t["id"], headers=s).status_code == 403
    assert env.client.post("/api/v1/tickets/%d/transition" % t["id"], headers=s,
                           json={"target": "Assigned", "expected_version": 1}).status_code == 403
    assert env.client.get("/api/v1/tickets/%d/audit" % t["id"], headers=s).status_code == 403
    assert env.scalar("SELECT state FROM tickets WHERE id=?", t["id"]) == "New"


def test_S7_student_and_faculty_cannot_inject_sensor_events(env):
    ev = {"source": "x", "event_id": "1", "facility": "ROOM-101", "metric": "temperature", "value": 50}
    for role in ("student", "faculty", "approver"):
        assert env.client.post("/api/v1/sensor-events", json=ev, headers=env.h(role)).status_code == 403
    assert env.count("tickets") == 0


def test_S8_sql_metacharacters_are_stored_as_data(env):
    evil = "x'); DROP TABLE tickets;--"
    r = env.client.post("/api/v1/tickets", json={"title": evil, "impact": "Low", "urgency": "Low"},
                        headers=env.h("faculty"))
    assert r.status_code == 201 and env.count("tickets") == 1
    assert env.scalar("SELECT title FROM tickets") == evil


def test_S9_errors_do_not_leak_internals(env):
    r = env.client.post("/api/v1/tickets", data="not json", headers=env.h("faculty"))
    assert r.status_code == 400 and "Traceback" not in r.get_data(as_text=True)


def test_S10_app_refuses_to_start_without_secret_from_environment(monkeypatch, tmp_path):
    from campus.app import create_app
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app({"SECRET_KEY": None, "DB_PATH": str(tmp_path / "x.db")})
