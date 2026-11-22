import unittest
from demonstrator import credentials as cr

KEY = b"k" * 32
CERT = {"student": "s1", "grade": "A"}


class TestCredentials(unittest.TestCase):
    def test_retry_then_issue_once(self):
        svc = cr.CredentialService(KEY, cr.ExternalVerifier(fail_first_n=2))
        self.assertEqual(svc.request_issue("k1", CERT), "issued")
        self.assertEqual(svc.request_issue("k1", CERT), "already_issued")
        self.assertEqual(len(svc.issued), 1)

    def test_pending_when_down_then_recovers(self):
        v = cr.ExternalVerifier(always_down=True)
        svc = cr.CredentialService(KEY, v)
        self.assertEqual(svc.request_issue("k1", CERT), "pending_retry")
        v.always_down = False
        self.assertEqual(svc.request_issue("k1", CERT), "issued")
        self.assertFalse(svc.pending)

    def test_tamper_rejected(self):
        svc = cr.CredentialService(KEY, cr.ExternalVerifier())
        svc.request_issue("k1", CERT)
        pkg = svc.issued["k1"]
        self.assertTrue(svc.employer_check(pkg))
        bad = {"cert": dict(pkg["cert"], grade="O"), "sig": pkg["sig"]}
        self.assertFalse(svc.employer_check(bad))
