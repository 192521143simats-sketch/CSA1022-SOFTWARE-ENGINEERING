"""Role-controlled examination workflow with human authority, recorded overrides,
versioned corrections, student dispute and redacted export.

Blind-first evaluation: the examiner records a provisional mark BEFORE the
assistant's suggestion is revealed (reduces anchoring). The suggestion can never
approve, publish or change a mark.
"""
import re

from . import BANDS, MANUAL
from . import matrix, rubric
from .audit import AuditLog

DISPUTE_WINDOW_DAYS = 7  # planning assumption


class Forbidden(Exception):
    """Actor's role is not allowed to perform the action."""


class Rejected(Exception):
    """Action is allowed for the role but violates a business rule."""


ROLE_PERMS = {
    "assistant":  {"suggest"},                       # system component: suggest only
    "examiner":   {"evaluate", "view_assigned"},
    "moderator":  {"moderate", "view_evaluated"},
    "controller": {"approve", "correct", "view_all"},
    "student":    {"view_own", "dispute"},
    "committee":  {"resolve_dispute"},
    "dpo":        {"erase"},
    "export_worker": {"export_redacted"},
    "administrator": {"manage_users"},
}

ID_PATTERNS = [
    re.compile(r"\b\d{2}[A-Za-z]{2,5}\d{2,5}\b"),          # register number like 21CSE1234
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),                 # e-mail
    re.compile(r"\b\d{10}\b"),                              # phone-like
]


def mark_to_band(mark):
    return "High" if mark >= 7 else "Medium" if mark >= 4 else "Low"


def redact(text, extra_ids=()):
    n = 0
    for pat in ID_PATTERNS:
        text, k = pat.subn("[REDACTED]", text)
        n += k
    for ident in extra_ids:
        if ident and ident in text:
            text = text.replace(ident, "[REDACTED]")
            n += 1
    return text, n


class ExamWorkflow:
    def __init__(self, rub=None, version="v2"):
        self.rub = rub or rubric.load_rubric()
        self.version = version
        self.audit = AuditLog()
        self.records = {}
        self.denied = []                 # log of refused attempts (for evidence)

    # -- helpers ---------------------------------------------------------
    def _need(self, role, perm):
        if perm not in ROLE_PERMS.get(role, set()):
            self.denied.append((role, perm))
            raise Forbidden(f"role '{role}' may not '{perm}'")

    def _rec(self, answer_id):
        if answer_id not in self.records:
            raise Rejected(f"unknown answer {answer_id}")
        return self.records[answer_id]

    def _version(self, rec, actor, role, action, mark, reason):
        idx = self.audit.append(role, action, {"answer": rec["answer_id"], "mark": mark,
                                               "reason": reason})["index"]
        v = {"version": len(rec["versions"]) + 1, "actor": actor, "role": role,
             "action": action, "mark": mark, "reason": reason, "audit_index": idx}
        rec["versions"].append(v)
        return v

    # -- steps -----------------------------------------------------------
    def submit(self, answer_id, student_id, examiner_id, text):
        self.records[answer_id] = {"answer_id": answer_id, "student": student_id,
                                   "examiner": examiner_id, "text": text,
                                   "state": "SUBMITTED", "versions": [],
                                   "suggestion": None, "priority": None,
                                   "approved_day": None}

    def assistant_suggestion(self, answer_id):
        """Computed only AFTER the examiner's provisional mark (blind-first)."""
        rec = self._rec(answer_id)
        return rubric.assist(rec["text"], self.rub, self.version)

    def suggest_as(self, role, answer_id):
        self._need(role, "suggest")
        return self.assistant_suggestion(answer_id)

    def evaluate(self, user, role, answer_id, mark, reason="", stakes="Low"):
        self._need(role, "evaluate")
        rec = self._rec(answer_id)
        if rec["examiner"] != user:
            self.denied.append((role, "evaluate_unassigned"))
            raise Forbidden("examiner is not assigned to this script")
        if rec["state"] != "SUBMITTED":
            raise Rejected(f"cannot evaluate in state {rec['state']}")
        band = mark_to_band(mark)
        sug = self.assistant_suggestion(answer_id)          # revealed after mark entered
        shown = sug["band"] if sug["band"] in BANDS else None
        if shown and shown != band and not reason.strip():
            raise Rejected("override of a shown suggestion requires a reason")
        rec["suggestion"] = sug
        rec["priority"] = matrix.moderation_priority(stakes, band, sug["band"])
        self._version(rec, user, role, "evaluate", mark, reason)
        rec["state"] = "EVALUATED"
        return rec["priority"]

    def moderate(self, user, role, answer_id, note=""):
        self._need(role, "moderate")
        rec = self._rec(answer_id)
        if rec["state"] != "EVALUATED":
            raise Rejected(f"cannot moderate in state {rec['state']}")
        self._version(rec, user, role, "moderate", rec["versions"][-1]["mark"], note)
        rec["state"] = "MODERATED"

    def approve(self, user, role, answer_id, day=0):
        self._need(role, "approve")
        rec = self._rec(answer_id)
        if rec["state"] != "MODERATED":
            raise Rejected(f"cannot approve in state {rec['state']}")
        self._version(rec, user, role, "approve", rec["versions"][-1]["mark"], "")
        rec["state"] = "APPROVED"
        rec["approved_day"] = day

    def dispute(self, user, role, answer_id, reason, day):
        self._need(role, "dispute")
        rec = self._rec(answer_id)
        if rec["student"] != user:
            self.denied.append((role, "dispute_other_student"))
            raise Forbidden("student may only dispute their own record")
        if rec["state"] != "APPROVED":
            raise Rejected(f"cannot dispute in state {rec['state']}")
        if day - rec["approved_day"] > DISPUTE_WINDOW_DAYS:
            raise Rejected("dispute window closed")
        if not reason.strip():
            raise Rejected("dispute requires a reason")
        self._version(rec, user, role, "dispute", rec["versions"][-1]["mark"], reason)
        rec["state"] = "DISPUTED"

    def correct(self, user, role, answer_id, new_mark, reason):
        self._need(role, "correct")
        rec = self._rec(answer_id)
        if rec["state"] not in ("APPROVED", "DISPUTED"):
            raise Rejected(f"cannot correct in state {rec['state']}")
        if not reason.strip():
            raise Rejected("correction requires a recorded reason")
        self._version(rec, user, role, "correct", new_mark, reason)
        rec["state"] = "CORRECTED"

    def current_mark(self, answer_id):
        return self._rec(answer_id)["versions"][-1]["mark"]

    # -- access ----------------------------------------------------------
    def view(self, user, role, answer_id):
        rec = self._rec(answer_id)
        if role == "examiner":
            self._need(role, "view_assigned")
            ok = rec["examiner"] == user
        elif role == "student":
            self._need(role, "view_own")
            ok = rec["student"] == user
        elif role == "moderator":
            self._need(role, "view_evaluated")
            ok = rec["state"] != "SUBMITTED"
        elif role == "controller":
            self._need(role, "view_all")
            ok = True
        else:
            self.denied.append((role, "view"))
            raise Forbidden(f"role '{role}' has no view access")
        if not ok:
            self.denied.append((role, "view_out_of_scope"))
            raise Forbidden("record outside this actor's scope")
        return {"answer_id": rec["answer_id"], "state": rec["state"],
                "mark": rec["versions"][-1]["mark"] if rec["versions"] else None}

    # -- right to erasure of superseded sensitive values ----------------
    def erase_superseded(self, user, role, answer_id, version_no, reason):
        self._need(role, "erase")
        rec = self._rec(answer_id)
        if not reason.strip():
            raise Rejected("erasure requires a recorded reason")
        if version_no >= len(rec["versions"]):
            raise Rejected("cannot erase the current mark")
        v = rec["versions"][version_no - 1]
        self.audit.erase_content(v["audit_index"])
        v["mark"] = None
        v["reason"] = "[erased]"
        self._version(rec, user, role, "erase_content", rec["versions"][-1]["mark"],
                      f"erased version {version_no}: {reason}")

    # -- redacted export for evaluation datasets ------------------------
    def export_redacted(self, role):
        self._need(role, "export_redacted")
        out, hits = [], 0
        for rec in self.records.values():
            text, n = redact(rec["text"], extra_ids=(rec["student"], rec["examiner"]))
            hits += n
            out.append({"answer_id": rec["answer_id"], "text": text})
        return out, hits

    def moderation_queue(self):
        rank = matrix.PRIORITY_RANK
        evald = [r for r in self.records.values() if r["state"] == "EVALUATED"]
        return sorted(evald, key=lambda r: (-rank[r["priority"]], r["answer_id"]))
