"""External adapters (issue tracker, calendar). Every remote call carries a stable
idempotency key so a retry can never create a second remote object."""
import json
import urllib.request


class TrackerError(Exception):
    pass


class FakeTracker:
    """Controlled stand-in used by tests and the isolated deployment.
    modes: ok | down (raises) | timeout-after-create (creates remotely, then fails)."""

    def __init__(self, mode="ok"):
        self.mode = mode
        self.issues = {}  # idempotency_key -> remote id
        self.calls = 0

    def create_issue(self, key, title):
        self.calls += 1
        if self.mode == "down":
            raise TrackerError("service unavailable")
        if key not in self.issues:
            self.issues[key] = "REMOTE-%d" % (len(self.issues) + 1)
        if self.mode == "timeout-after-create":
            raise TrackerError("timeout after remote create")
        return self.issues[key]

    def send(self, key, payload):
        return self.create_issue(key, payload.get("title", ""))


class FakeCalendar(FakeTracker):
    """Same failure modes; remote ids look like calendar events."""

    def create_issue(self, key, title):
        remote = super().create_issue(key, title)
        return remote.replace("REMOTE", "EVENT")


class HttpTracker:
    """Minimal real adapter (not exercised against a live service in this work)."""

    def __init__(self, url, token, timeout=3):
        if not url.startswith(("https://", "http://")):
            raise ValueError("URL must be http(s)")   # blocks file:/ and custom schemes
        self.url, self.token, self.timeout = url, token, timeout

    def send(self, key, payload):
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode(), method="POST",
            headers={"Authorization": "Bearer " + self.token,
                     "Idempotency-Key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:  # nosec B310
                return json.loads(r.read())["id"]
        except Exception as exc:
            raise TrackerError(str(exc))
