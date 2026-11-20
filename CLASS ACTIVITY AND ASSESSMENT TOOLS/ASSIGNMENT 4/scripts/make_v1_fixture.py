"""Deterministic SYNTHETIC release-1.0 database (schema 001 only) for migration rehearsals.
usage: python scripts/make_v1_fixture.py <path> [bookings] [tickets]"""
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from campus.db import migrate  # noqa: E402


def make(path, n_bookings=200, n_tickets=120, seed=42):
    migrate(path, max_version=1)
    rnd = random.Random(seed)
    c = sqlite3.connect(path)
    base = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
    f = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    for i in range(n_bookings):
        fac = rnd.choice([1, 2, 3, 3, 3])                           # HALL-A (id 3) is common
        start = base + timedelta(days=i, hours=rnd.choice([0, 2, 4]))
        mins = 180 if i % 7 == 0 else rnd.choice([30, 60, 90, 120])  # 180 is legal under release 1.0
        status = rnd.choice(["Pending", "Approved", "Approved", "Rejected"])
        c.execute("INSERT INTO bookings(facility_id,requester,title,start_utc,end_utc,status,created_utc)"
                  " VALUES(?,?,?,?,?,?,?)", (fac, "user%d" % rnd.randint(1, 30), "Booking %d" % i,
                                              f(start), f(start + timedelta(minutes=mins)), status, f(base)))
        c.execute("INSERT INTO audit(booking_id,action,to_state,actor,role,at_utc) VALUES(?,?,?,?,?,?)",
                  (i + 1, "booking.create", "Pending", "user", "faculty", f(base)))
    cats = ["Facilities", "HVAC", "AV-Network", "Manual Review"]
    states = ["New", "Assigned", "In Progress", "Resolved", "Closed"]
    for i in range(n_tickets):
        synced = i % 3 == 0
        c.execute("INSERT INTO tickets(title,description,category,impact,urgency,priority,state,version,notes,"
                  "source,event_id,facility_id,reporter,created_utc,sla_due_utc,sync_status,remote_id) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  ("Ticket %d" % i, "synthetic", rnd.choice(cats), "High", "Medium", "M2",
                   rnd.choice(states), 1 + i % 4, None, "sensor-%d" % (i % 5) if i % 4 == 0 else None,
                   "evt-%d" % i if i % 4 == 0 else None, rnd.choice([1, 2, 3]), "user%d" % rnd.randint(1, 30),
                   f(base), f(base + timedelta(hours=8)), "Synced" if synced else "Pending",
                   "REMOTE-%d" % i if synced else None))
        c.execute("INSERT INTO audit(ticket_id,action,to_state,actor,role,at_utc) VALUES(?,?,?,?,?,?)",
                  (i + 1, "ticket.create", "New", "user", "faculty", f(base)))
    c.commit()
    c.close()


if __name__ == "__main__":
    make(sys.argv[1], *(int(x) for x in sys.argv[2:4]))
    print("fixture written:", sys.argv[1])
