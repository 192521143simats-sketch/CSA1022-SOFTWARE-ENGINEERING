"""Conventional signed-certificate issue with retry-safe external verification.

Ledger is excluded. A certificate is a canonical JSON record plus an HMAC-SHA256
signature (stand-in for an asymmetric digital signature, which a real deployment
would use so verifiers never hold the signing key). The external verification
page may be unavailable: the local mark record is never touched, the request
stays pending and is retried with an idempotency key (no duplicate certificates).
"""
import hashlib
import hmac
import json


class Unavailable(Exception):
    pass


def canonical(d):
    return json.dumps(d, sort_keys=True, separators=(",", ":"))


def sign(cert, key):
    return hmac.new(key, canonical(cert).encode(), hashlib.sha256).hexdigest()


def issue(cert, key):
    return {"cert": dict(cert), "sig": sign(cert, key)}


def verify(pkg, key):
    return hmac.compare_digest(pkg["sig"], sign(pkg["cert"], key))


def fingerprint(pkg):
    return hashlib.sha256(canonical(pkg["cert"]).encode()).hexdigest()


class ExternalVerifier:
    """Simulated public verification page. Fails the first `fail_first_n` calls."""

    def __init__(self, fail_first_n=0, always_down=False):
        self.fail_first_n = fail_first_n
        self.always_down = always_down
        self.calls = 0
        self.published = set()

    def publish(self, fp):
        self.calls += 1
        if self.always_down or self.calls <= self.fail_first_n:
            raise Unavailable("verification service unavailable")
        self.published.add(fp)

    def is_published(self, fp):
        return fp in self.published


class CredentialService:
    def __init__(self, key, verifier, max_attempts=5):
        self.key, self.verifier, self.max_attempts = key, verifier, max_attempts
        self.issued, self.pending, self.attempt_log = {}, {}, []

    def request_issue(self, idem_key, fields):
        if idem_key in self.issued:                      # idempotent: no duplicate
            return "already_issued"
        pkg = self.pending.get(idem_key) or issue(fields, self.key)
        fp = fingerprint(pkg)
        for attempt in range(1, self.max_attempts + 1):
            try:
                self.verifier.publish(fp)
                self.issued[idem_key] = pkg
                self.pending.pop(idem_key, None)
                self.attempt_log.append((idem_key, attempt, "ok"))
                return "issued"
            except Unavailable:
                self.attempt_log.append((idem_key, attempt, "unavailable"))
        self.pending[idem_key] = pkg                    # keep for a later retry
        return "pending_retry"

    def employer_check(self, pkg):
        """What an external verifier would do: signature valid AND fingerprint published."""
        return verify(pkg, self.key) and self.verifier.is_published(fingerprint(pkg))
