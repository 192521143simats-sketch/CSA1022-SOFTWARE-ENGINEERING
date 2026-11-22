import copy
import unittest
from demonstrator import audit


def build(n=8, **kw):
    log = audit.AuditLog(**kw)
    for i in range(n):
        log.append("examiner", "evt", {"i": i, "mark": i})
    return log


class TestAudit(unittest.TestCase):
    def test_clean_verifies(self):
        self.assertTrue(build().verify()[0])

    def test_naive_edit_detected(self):
        l = build()
        l.entries[3]["payload"] = "x"
        ok, bad, _ = l.verify()
        self.assertFalse(ok)
        self.assertEqual(bad, 3)

    def test_privileged_rewrite_needs_checkpoint(self):
        l = build()
        head, n = l.head()
        audit.privileged_rewrite(l, 3, {"i": 3, "mark": 99})
        self.assertTrue(l.verify()[0])
        self.assertFalse(l.verify(head, n)[0])

    def test_truncation_needs_checkpoint(self):
        l = build()
        head, n = l.head()
        audit.truncate(l, 2)
        self.assertTrue(l.verify()[0])
        self.assertFalse(l.verify(head, n)[0])

    def test_erasure_keeps_chain_with_commitments(self):
        l = build()
        l.erase_content(2)
        self.assertTrue(l.verify()[0])
        self.assertIsNone(l.content_matches_commitment(2))

    def test_erasure_breaks_chain_when_content_hashed_in(self):
        l = build(content_in_chain=True)
        l.entries[2]["payload"] = "null"
        self.assertFalse(l.verify()[0])

    def test_salt_blocks_dictionary_attack(self):
        l = build()
        table = {audit._h("unsalted", '{"mark": %d}' % m): m for m in range(11)}
        self.assertNotIn(l.entries[0]["payload"], table)

    def test_commitment_matches_content(self):
        l = build()
        self.assertTrue(all(l.content_matches_commitment(i) for i in range(len(l.entries))))
