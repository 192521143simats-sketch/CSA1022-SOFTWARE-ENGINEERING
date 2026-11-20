"""Use-case layer: rules + persistence + authorisation, one function per command (release 2.0)."""
from datetime import timedelta

from . import auth, integration, policy, rules
from .db import tx


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


class Forbidden(Exception):
    pass


def _audit(db, now, actor, role, action, ticket_id=None, booking_id=None,
           from_state=None, to_state=None):
    db.execute(
        "INSERT INTO audit(ticket_id,booking_id,action,from_state,to_state,actor,role,at_utc)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (ticket_id, booking_id, action, from_state, to_state, actor, role, rules.fmt_utc(now)))


def _facility(db, code):
    row = db.execute("SELECT * FROM facilities WHERE code=?", (code,)).fetchone()
    if not row:
        raise NotFound("unknown facility")
    return row


def _need(role, perm):
    if not auth.allowed(role, perm):
        raise Forbidden("role %r lacks %s" % (role, perm))


def _text(value, name, maxlen=200):
    if not isinstance(value, str) or not value.strip():
        raise rules.RuleError("%s is required" % name)
    if len(value) > maxlen:
        raise rules.RuleError("%s too long" % name)
    return value.strip()


# ------------------------------------------------------------------ bookings
def booking_dict(r):
    """Release-1 response shape (kept unchanged for old clients)."""
    return {"id": r["id"], "facility": r["code"], "requester": r["requester"],
            "title": r["title"], "start": r["start_utc"], "end": r["end_utc"],
            "status": r["status"]}


def booking_dict_v2(r):
    s, e = rules.parse_utc(r["start_utc"]), rules.parse_utc(r["end_utc"])
    return {"id": r["id"], "facility": r["code"], "campus": r["campus_code"],
            "requester": r["requester"], "purpose": r["title"], "start": r["start_utc"],
            "end": r["end_utc"], "duration_minutes": int((e - s).total_seconds() // 60),
            "status": r["status"], "policy_version": r["policy_version"],
            "calendar_status": r["calendar_status"]}


def _booking_row(db, bid):
    return db.execute(
        "SELECT b.*, f.code, f.restricted FROM bookings b JOIN facilities f "
        "ON f.id=b.facility_id WHERE b.id=?", (bid,)).fetchone()


def create_booking(db, now, user, role, body, shape=booking_dict):
    _need(role, "booking:create")
    title = _text(body.get("title"), "title")
    fac = _facility(db, _text(body.get("facility"), "facility"))
    if fac["restricted"] and role == "student":
        raise Forbidden("students may not book restricted facilities")
    pol = policy.select_policy(policy.load_policies(db), fac["campus_code"])
    s, e = rules.parse_utc(body.get("start")), rules.parse_utc(body.get("end"))
    if e <= s:
        raise rules.RuleError("end must be after start")
    if not rules.valid_duration(int((e - s).total_seconds() // 60), pol["max_minutes"]) \
            or (e - s).total_seconds() % 60:
        raise rules.RuleError("duration outside policy (max %d minutes for campus %s)"
                              % (pol["max_minutes"], pol["campus_code"]))
    if s < now:
        raise rules.RuleError("start is in the past")
    with tx(db):
        clash = db.execute(
            "SELECT id FROM bookings WHERE facility_id=? AND status IN ('Pending','Approved')"
            " AND start_utc < ? AND ? < end_utc",
            (fac["id"], rules.fmt_utc(e), rules.fmt_utc(s))).fetchone()
        if clash:
            raise Conflict("overlapping booking %d" % clash["id"])
        cur = db.execute(
            "INSERT INTO bookings(facility_id,requester,title,start_utc,end_utc,status,created_utc,"
            "campus_code,policy_version) VALUES(?,?,?,?,?,'Pending',?,?,?)",
            (fac["id"], user, title, rules.fmt_utc(s), rules.fmt_utc(e), rules.fmt_utc(now),
             pol["campus_code"], pol["policy_version"]))
        _audit(db, now, user, role, "booking.create", booking_id=cur.lastrowid, to_state="Pending")
    return shape(_booking_row(db, cur.lastrowid))


def create_booking_v2(db, now, user, role, body):
    """Revised API: facility + purpose + start + duration_minutes."""
    d = body.get("duration_minutes")
    if isinstance(d, bool) or not isinstance(d, int) or d <= 0:
        raise rules.RuleError("duration_minutes must be a positive integer")
    start = rules.parse_utc(body.get("start"))
    mapped = {"facility": body.get("facility"), "title": body.get("purpose"),
              "start": rules.fmt_utc(start), "end": rules.fmt_utc(start + timedelta(minutes=d))}
    return create_booking(db, now, user, role, mapped, shape=booking_dict_v2)


def get_booking(db, user, role, bid, shape=booking_dict):
    r = _booking_row(db, bid)
    if not r:
        raise NotFound("booking not found")
    if r["requester"] != user and not auth.allowed(role, "booking:read_any"):
        raise Forbidden("not your booking")
    return shape(r)


def list_bookings(db, user, role, facility=None):
    q = ("SELECT b.*, f.code, f.restricted FROM bookings b JOIN facilities f "
         "ON f.id=b.facility_id WHERE 1=1")
    args = []
    if facility:
        q += " AND f.code=?"
        args.append(facility)
    if not auth.allowed(role, "booking:read_any"):
        q += " AND b.requester=?"
        args.append(user)
    return [booking_dict(r) for r in db.execute(q + " ORDER BY b.id", args)]


def approve_booking(db, now, user, role, bid, adapters, shape=booking_dict):
    _need(role, "booking:approve")
    with tx(db):
        r = _booking_row(db, bid)
        if not r:
            raise NotFound("booking not found")
        if r["restricted"]:
            _need(role, "booking:approve_restricted")
        if r["status"] != "Pending":
            raise Conflict("booking is %s" % r["status"])
        db.execute("UPDATE bookings SET status='Approved', calendar_status='Pending' WHERE id=?", (bid,))
        integration.enqueue(db, now, "calendar", bid)               # durable intent, same transaction
        _audit(db, now, user, role, "booking.approve", booking_id=bid,
               from_state="Pending", to_state="Approved")
    integration.attempt_for(db, now, adapters, "calendar", bid)    # best effort now, retried later
    return shape(_booking_row(db, bid))


# ------------------------------------------------------------------- tickets
def ticket_dict(db, r, now):
    due = rules.parse_utc(r["sla_due_utc"])
    return {"id": r["id"], "title": r["title"], "category": r["category"],
            "impact": r["impact"], "urgency": r["urgency"], "priority": r["priority"],
            "state": r["state"], "version": r["version"], "notes": r["notes"],
            "reporter": r["reporter"], "facility": r["code"],
            "sla_due": r["sla_due_utc"], "overdue": rules.is_overdue(now, due),
            "sync_status": r["sync_status"], "remote_id": r["remote_id"]}


def _ticket_row(db, tid):
    return db.execute(
        "SELECT t.*, f.code, f.restricted FROM tickets t LEFT JOIN facilities f "
        "ON f.id=t.facility_id WHERE t.id=?", (tid,)).fetchone()


def _insert_ticket(db, now, user, role, title, description, impact, urgency, fac,
                   source=None, event_id=None):
    prio = rules.priority(impact, urgency)
    cat = rules.classify("%s %s" % (title, description or ""))
    pol = policy.select_policy(policy.load_policies(db), fac["campus_code"] if fac else None)
    cur = db.execute(
        "INSERT INTO tickets(title,description,category,impact,urgency,priority,state,version,"
        "source,event_id,facility_id,reporter,created_utc,sla_due_utc,campus_code,policy_version) "
        "VALUES(?,?,?,?,?,?,'New',1,?,?,?,?,?,?,?,?)",
        (title, description, cat, impact, urgency, prio, source, event_id, fac["id"] if fac else None,
         user, rules.fmt_utc(now), rules.fmt_utc(rules.sla_due(now, prio)),
         pol["campus_code"], pol["policy_version"]))
    _audit(db, now, user, role, "ticket.create", ticket_id=cur.lastrowid, to_state="New")
    integration.enqueue(db, now, "issue", cur.lastrowid)            # durable intent, same transaction
    return cur.lastrowid


def create_ticket(db, now, user, role, body, adapters):
    _need(role, "ticket:create")
    title = _text(body.get("title"), "title")
    desc = body.get("description") or ""
    if not isinstance(desc, str) or len(desc) > 2000:
        raise rules.RuleError("description invalid")
    fac = _facility(db, body["facility"]) if body.get("facility") else None
    with tx(db):
        tid = _insert_ticket(db, now, user, role, title, desc, body.get("impact"),
                             body.get("urgency"), fac)
    integration.attempt_for(db, now, adapters, "issue", tid)
    return ticket_dict(db, _ticket_row(db, tid), now)


def get_ticket(db, now, user, role, tid):
    r = _ticket_row(db, tid)
    if not r:
        raise NotFound("ticket not found")
    if not auth.allowed(role, "ticket:read_any"):
        if r["reporter"] != user or r["restricted"]:
            raise Forbidden("ticket not accessible")
    return ticket_dict(db, r, now)


def transition_ticket(db, now, user, role, tid, body):
    _need(role, "ticket:transition")
    target, expected = body.get("target"), body.get("expected_version")
    if not isinstance(target, str) or not isinstance(expected, int) or isinstance(expected, bool):
        raise rules.RuleError("target and integer expected_version are required")
    with tx(db):
        r = _ticket_row(db, tid)
        if not r:
            raise NotFound("ticket not found")
        if r["version"] != expected:
            raise Conflict("stale version: current is %d" % r["version"])
        rules.check_transition(r["state"], target, body.get("notes"))
        db.execute("UPDATE tickets SET state=?, version=version+1, notes=COALESCE(?,notes) "
                   "WHERE id=? AND version=?", (target, body.get("notes"), tid, expected))
        _audit(db, now, user, role, "ticket.transition", ticket_id=tid,
               from_state=r["state"], to_state=target)
    return ticket_dict(db, _ticket_row(db, tid), now)


def ticket_audit(db, role, tid):
    _need(role, "audit:read")
    return [dict(r) for r in db.execute(
        "SELECT action,from_state,to_state,actor,role,at_utc FROM audit "
        "WHERE ticket_id=? ORDER BY id", (tid,))]


# --------------------------------------------------------------- sensor events
def ingest_sensor(db, now, user, role, body, adapters):
    _need(role, "sensor:ingest")
    source = _text(body.get("source"), "source", 60)
    event_id = _text(body.get("event_id"), "event_id", 100)
    fac = _facility(db, _text(body.get("facility"), "facility"))
    if body.get("metric") != "temperature":
        raise rules.RuleError("unsupported metric")
    value = body.get("value")
    if isinstance(value, bool) or value is None:
        raise rules.RuleError("value required")
    pol = policy.select_policy(policy.load_policies(db), fac["campus_code"])
    if not rules.breached(value, pol["temp_limit"]):
        return {"breach": False, "duplicate": False, "ticket_id": None}, 200
    impact = "High" if fac["restricted"] else "Medium"
    with tx(db):
        old = db.execute("SELECT id FROM tickets WHERE source=? AND event_id=?",
                         (source, event_id)).fetchone()
        if old:
            return {"breach": True, "duplicate": True, "ticket_id": old["id"]}, 200
        tid = _insert_ticket(
            db, now, user, role, "Temperature breach %s: %s" % (fac["code"], value),
            "temperature cooling alert from %s" % source, impact, "High", fac,
            source, event_id)
    integration.attempt_for(db, now, adapters, "issue", tid)
    return {"breach": True, "duplicate": False, "ticket_id": tid}, 201


# ------------------------------------------------------------ integration admin
def sync_ticket(db, now, user, role, tid, adapters):
    _need(role, "integration:sync")
    if not _ticket_row(db, tid):
        raise NotFound("ticket not found")
    integration.attempt_for(db, now, adapters, "issue", tid, force=True)
    return ticket_dict(db, _ticket_row(db, tid), now)


def flush_integrations(db, now, role, adapters):
    _need(role, "integration:sync")
    return integration.flush(db, now, adapters)


def integration_status(db, now, role):
    _need(role, "integration:sync")
    return integration.status(db, now)
