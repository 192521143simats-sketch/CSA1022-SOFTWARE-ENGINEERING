"""Hash-chained audit log with salted commitments (tamper-EVIDENT, not tamper-proof).

Design (revision R2): the chain stores a salted commitment of the sensitive
content; the content and salt live in a restricted store. Erasing content
therefore does not break the chain. Mode content_in_chain=True reproduces the
naive design (content hashed straight into the chain) for test T7a.
"""
import hashlib
import json
import os

GENESIS = "0" * 64


def _h(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def commit(content, salt):
    return _h("commit", salt, json.dumps(content, sort_keys=True))


class AuditLog:
    def __init__(self, content_in_chain=False, rng_bytes=os.urandom):
        self.entries = []          # public chain
        self.restricted = {}       # index -> {"salt":..., "content":...}  (restricted DB)
        self.content_in_chain = content_in_chain
        self._rng = rng_bytes

    # -- append ----------------------------------------------------------
    def append(self, actor, action, content):
        idx = len(self.entries)
        prev = self.entries[-1]["hash"] if self.entries else GENESIS
        salt = self._rng(8).hex()
        if self.content_in_chain:
            payload = json.dumps(content, sort_keys=True)
        else:
            payload = commit(content, salt)
        entry = {"index": idx, "actor": actor, "action": action,
                 "payload": payload, "prev": prev}
        entry["hash"] = self._entry_hash(entry)
        self.entries.append(entry)
        self.restricted[idx] = {"salt": salt, "content": content}
        return entry

    @staticmethod
    def _entry_hash(e):
        return _h(e["index"], e["actor"], e["action"], e["payload"], e["prev"])

    # -- verify ----------------------------------------------------------
    def verify(self, external_head=None, external_length=None):
        """Return (ok, first_bad_index, reason). Internal consistency first,
        then comparison with an externally held head hash and length."""
        prev = GENESIS
        for e in self.entries:
            if e["prev"] != prev or e["hash"] != self._entry_hash(e):
                return False, e["index"], "chain_broken"
            prev = e["hash"]
        if external_head is not None:
            head = self.entries[-1]["hash"] if self.entries else GENESIS
            if external_length is not None and len(self.entries) != external_length:
                return False, len(self.entries), "length_mismatch_vs_checkpoint"
            if head != external_head:
                return False, len(self.entries) - 1, "head_mismatch_vs_checkpoint"
        return True, None, "ok"

    def head(self):
        return (self.entries[-1]["hash"] if self.entries else GENESIS, len(self.entries))

    # -- restricted content ---------------------------------------------
    def content_matches_commitment(self, idx):
        """True/False if content is present; None if it was erased."""
        r = self.restricted.get(idx)
        if r is None or r["content"] is None:
            return None
        return commit(r["content"], r["salt"]) == self.entries[idx]["payload"]

    def erase_content(self, idx):
        """Right-to-erasure: remove content and salt, keep commitment + metadata."""
        self.restricted[idx] = {"salt": None, "content": None}
        return True


# -- attacker helpers used only by tests/demonstrator -------------------------
def privileged_rewrite(log, index, new_content, recompute=True):
    """Simulate an administrator editing an entry. With recompute the attacker
    also rebuilds every later hash so the internal chain still verifies."""
    e = log.entries[index]
    if log.content_in_chain:
        e["payload"] = json.dumps(new_content, sort_keys=True)
    else:
        salt = log.restricted[index]["salt"]
        e["payload"] = commit(new_content, salt)
        log.restricted[index]["content"] = new_content
    if recompute:
        prev = log.entries[index - 1]["hash"] if index else GENESIS
        for e2 in log.entries[index:]:
            e2["prev"] = prev
            e2["hash"] = AuditLog._entry_hash(e2)
            prev = e2["hash"]


def truncate(log, n_last):
    del log.entries[-n_last:]


def dictionary_attack_unsalted(commitments_unsalted, candidates):
    """Recover low-entropy values (e.g. marks 0..10) from UNSALTED hashes."""
    table = {_h("unsalted", json.dumps({"mark": c}, sort_keys=True)): c for c in candidates}
    return [table.get(c) for c in commitments_unsalted]
