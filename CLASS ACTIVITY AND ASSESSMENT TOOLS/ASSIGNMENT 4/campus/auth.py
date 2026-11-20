"""Signed bearer tokens. Identity and role come ONLY from the verified token,
never from request bodies or headers."""
import base64
import hashlib
import hmac

ROLES = {"admin", "manager", "technician", "approver", "faculty", "student", "sensor"}
STAFF = {"admin", "manager", "technician", "approver"}

PERMS = {
    "booking:create": ROLES - {"sensor"},
    "booking:read_any": STAFF,
    "booking:approve": {"approver", "manager", "admin"},
    "booking:approve_restricted": {"manager", "admin"},
    "ticket:create": ROLES - {"sensor"},
    "ticket:read_any": STAFF,
    "ticket:transition": {"technician", "manager", "admin"},
    "sensor:ingest": {"sensor", "technician", "manager", "admin"},
    "integration:sync": {"technician", "manager", "admin"},
    "audit:read": {"manager", "admin"},
}


class AuthError(Exception):
    pass


def _sig(secret, payload):
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def issue_token(secret, user, role, now_ts, ttl=3600):
    if role not in ROLES:
        raise AuthError("unknown role")
    payload = "%s|%s|%d" % (user, role, int(now_ts) + ttl)
    body = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return body + "." + _sig(secret, body)


def verify_token(secret, token, now_ts):
    try:
        body, sig = token.rsplit(".", 1)
    except (ValueError, AttributeError):
        raise AuthError("malformed token")
    if not hmac.compare_digest(sig, _sig(secret, body)):
        raise AuthError("bad signature")
    try:
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode()
        user, role, exp = raw.split("|")
        exp = int(exp)
    except Exception:
        raise AuthError("malformed payload")
    if now_ts > exp:
        raise AuthError("token expired")
    if role not in ROLES:
        raise AuthError("unknown role")
    return user, role


def allowed(role, perm):
    return role in PERMS[perm]
