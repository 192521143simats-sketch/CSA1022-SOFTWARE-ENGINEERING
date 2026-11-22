import unittest
from demonstrator.workflow import ExamWorkflow, Forbidden, Rejected, redact

HIGH = ("Atomicity means a transaction is all or nothing. Consistency means the database keeps its "
        "constraints true. Isolation means concurrent transactions do not interfere with each other.")


def make():
    wf = ExamWorkflow()
    wf.submit("A1", "stu-1", "ex-1", HIGH)
    return wf


class TestWorkflow(unittest.TestCase):
    def test_assistant_cannot_approve(self):
        with self.assertRaises(Forbidden):
            make().approve("assistant", "assistant", "A1")

    def test_examiner_cannot_approve(self):
        wf = make()
        wf.evaluate("ex-1", "examiner", "A1", 8)
        wf.moderate("m", "moderator", "A1")
        with self.assertRaises(Forbidden):
            wf.approve("ex-1", "examiner", "A1")

    def test_cannot_skip_moderation(self):
        wf = make()
        wf.evaluate("ex-1", "examiner", "A1", 8)
        with self.assertRaises(Rejected):
            wf.approve("c", "controller", "A1")

    def test_override_needs_reason(self):
        with self.assertRaises(Rejected):
            make().evaluate("ex-1", "examiner", "A1", 2)

    def test_unassigned_examiner_forbidden(self):
        with self.assertRaises(Forbidden):
            make().evaluate("ex-2", "examiner", "A1", 8)

    def test_normal_path_and_correction_history(self):
        wf = make()
        wf.evaluate("ex-1", "examiner", "A1", 8)
        wf.moderate("m", "moderator", "A1")
        wf.approve("c", "controller", "A1", day=0)
        with self.assertRaises(Rejected):
            wf.correct("c", "controller", "A1", 9, "  ")
        wf.correct("c", "controller", "A1", 9, "re-read")
        self.assertEqual(len(wf.records["A1"]["versions"]), 4)
        self.assertEqual(wf.current_mark("A1"), 9)

    def test_dispute_window(self):
        wf = make()
        wf.evaluate("ex-1", "examiner", "A1", 8)
        wf.moderate("m", "moderator", "A1")
        wf.approve("c", "controller", "A1", day=0)
        with self.assertRaises(Rejected):
            wf.dispute("stu-1", "student", "A1", "late", day=8)
        wf.dispute("stu-1", "student", "A1", "ok", day=7)

    def test_redaction(self):
        t, n = redact("mail kumar@example.in reg 21CSE1234")
        self.assertEqual(n, 2)
        self.assertNotIn("21CSE1234", t)

    def test_audit_has_no_student_identifier(self):
        wf = make()
        wf.evaluate("ex-1", "examiner", "A1", 8)
        blob = str(wf.audit.restricted) + str(wf.audit.entries)
        self.assertNotIn("stu-1", blob)

    def test_cannot_erase_current_mark(self):
        wf = make()
        wf.evaluate("ex-1", "examiner", "A1", 8)
        with self.assertRaises(Rejected):
            wf.erase_superseded("d", "dpo", "A1", 1, "request")
