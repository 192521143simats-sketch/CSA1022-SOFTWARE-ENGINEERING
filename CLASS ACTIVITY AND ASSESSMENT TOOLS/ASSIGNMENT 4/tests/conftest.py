import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from campus import auth                      # noqa: E402
from campus.app import create_app            # noqa: E402
from campus.db import migrate                # noqa: E402
from campus.tracker import FakeCalendar, FakeTracker   # noqa: E402

SECRET = "test-secret-not-for-production"
NOW = datetime(2026, 11, 20, 8, 0, 0, tzinfo=timezone.utc)   # fixed clock


class Env:
    """Isolated environment: fresh SQLite file per test, fixed clock, fake tracker."""

    def __init__(self, path):
        self.path = str(path)
        migrate(self.path)
        self.tracker = FakeTracker("ok")
        self.calendar = FakeCalendar("ok")
        self.clock = NOW                      # tests may advance this
        self.app = self.make_app()
        self.client = self.app.test_client()

    def make_app(self):
        return create_app({"SECRET_KEY": SECRET, "DB_PATH": self.path,
                           "CLOCK": lambda: self.clock, "TRACKER": self.tracker,
                           "CALENDAR": self.calendar,
                           "TESTING": True})

    def restart(self):
        """Simulate a process restart on the same database file."""
        self.app = self.make_app()
        self.client = self.app.test_client()

    def h(self, role, user=None, ttl=3 * 86400):
        tok = auth.issue_token(SECRET, user or (role + "1"), role, NOW.timestamp(), ttl)
        return {"Authorization": "Bearer " + tok}

    def count(self, table):
        import sqlite3
        c = sqlite3.connect(self.path)
        try:
            return c.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
        finally:
            c.close()

    def scalar(self, sql, *args):
        import sqlite3
        c = sqlite3.connect(self.path)
        try:
            return c.execute(sql, args).fetchone()[0]
        finally:
            c.close()


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path / "campus.db")


def booking(facility="ROOM-101", start="2026-11-21T10:00:00Z", end="2026-11-21T11:00:00Z",
            title="Study group"):
    return {"facility": facility, "start": start, "end": end, "title": title}
