"""Campus-specific, versioned policies (release 2.0)."""
from .rules import RuleError

DEFAULT_CAMPUS = "MAIN"


def load_policies(db):
    return [dict(r) for r in db.execute(
        "SELECT campus_code, policy_version, max_minutes, temp_limit FROM policies")]


def select_policy(policies, campus, version=None):
    """Latest policy for a campus (or an exact recorded version).
    An unknown/missing campus falls back to the DEFAULT campus - never to 'no limit'."""
    mine = [p for p in policies if p["campus_code"] == (campus or DEFAULT_CAMPUS)]
    if not mine:
        mine = [p for p in policies if p["campus_code"] == DEFAULT_CAMPUS]
    if not mine:
        raise RuleError("no policy configured")
    if version is not None:
        exact = [p for p in mine if p["policy_version"] == version]
        if not exact:
            raise RuleError("unknown policy version %r" % (version,))
        return exact[0]
    return max(mine, key=lambda p: p["policy_version"])
