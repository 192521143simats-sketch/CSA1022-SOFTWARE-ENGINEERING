#!/usr/bin/env python3
"""Run every check of the demonstrator and write results/results.json (+ timing.json).

Usage:  python3 run_demonstrator.py            (standard library only, seed 2026)
Deterministic results go to results/results.json; machine-specific timing goes to
results/timing.json (a single-machine figure, not a production benchmark).
"""
import copy
import hashlib
import json
import math
import platform
import statistics
import sys
import time
from pathlib import Path

from demonstrator import BANDS, MANUAL, SEED
from demonstrator import audit, credentials, matrix, resources, rubric, selection, simulation
from demonstrator.workflow import ExamWorkflow, Forbidden, Rejected

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)


def hdr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


class DetRng:
    """Deterministic salt source so audit results are reproducible."""
    def __init__(self):
        self.i = 0

    def __call__(self, n):
        self.i += 1
        return hashlib.sha256(f"{SEED}-{self.i}".encode()).digest()[:n]


def verdict(ok):
    return "PASS" if ok else "FAIL"


# =============================================================================
def c2_assistant(rub, rows):
    hdr("C2  Rule assistant vs forced-choice baseline (24 synthetic answers, expert-labelled)")
    per = []
    print(f"{'id':>3} {'style':<18}{'expert':<8}{'baseline':<9}{'v1':<15}{'v2 (R1)':<15}{'v2 reason'}")
    for r in rows:
        b = rubric.baseline(r["text"], rub)
        v1 = rubric.assist(r["text"], rub, "v1")
        v2 = rubric.assist(r["text"], rub, "v2")
        per.append({"id": r["id"], "style": r["style"], "expert": r["expert_band"],
                    "baseline": b["band"], "v1": v1["band"], "v2": v2["band"],
                    "matched": b["matched"], "v1_reason": v1["reason"], "v2_reason": v2["reason"]})
        flag = lambda pred: "" if pred == r["expert_band"] else ("*" if pred != MANUAL else "")
        print(f"{r['id']:>3} {r['style']:<18}{r['expert_band']:<8}"
              f"{b['band'] + flag(b['band']):<9}{v1['band'] + flag(v1['band']):<15}"
              f"{v2['band'] + flag(v2['band']):<15}{v2['reason']}")
    print("(* = wrong suggestion)")

    def metrics(key):
        n = len(per)
        manual = sum(p[key] == MANUAL for p in per)
        answered = n - manual
        correct = sum(p[key] == p["expert"] for p in per)
        wrong = answered - correct
        lo, hi = wilson(wrong, answered)
        return {"n": n, "answered": answered, "manual_review": manual, "correct": correct,
                "wrong": wrong,
                "accuracy_on_answered": round(correct / answered, 3) if answered else None,
                "wrong_rate_on_answered": round(wrong / answered, 3) if answered else None,
                "wrong_rate_wilson95": [lo, hi],
                "coverage": round(answered / n, 3)}
    m = {k: metrics(k) for k in ("baseline", "v1", "v2")}
    print()
    print(f"{'method':<10}{'answered':>9}{'manual':>8}{'correct':>9}{'wrong':>7}"
          f"{'acc/ans':>9}{'coverage':>10}{'wrong-rate 95% CI':>22}")
    for k, v in m.items():
        print(f"{k:<10}{v['answered']:>9}{v['manual_review']:>8}{v['correct']:>9}{v['wrong']:>7}"
              f"{v['accuracy_on_answered']:>9.2f}{v['coverage']*100:>9.1f}%"
              f"{'  [%.2f, %.2f]' % tuple(v['wrong_rate_wilson95']):>22}")

    # fairness by answer style
    styles = sorted({p["style"] for p in per})
    by_style = {}
    print("\nBy answer style (fairness audit):  wrong/answered  [manual]")
    print(f"{'style':<20}{'n':>3}  {'baseline':<16}{'v1':<16}{'v2':<16}")
    for s in styles:
        sub = [p for p in per if p["style"] == s]
        row = {"n": len(sub)}
        cells = []
        for k in ("baseline", "v1", "v2"):
            man = sum(p[k] == MANUAL for p in sub)
            ans = len(sub) - man
            wr = sum(p[k] != p["expert"] for p in sub if p[k] != MANUAL)
            row[k] = {"wrong": wr, "answered": ans, "manual": man}
            cells.append(f"{wr}/{ans}  [{man}]")
        by_style[s] = row
        print(f"{s:<20}{len(sub):>3}  {cells[0]:<16}{cells[1]:<16}{cells[2]:<16}")

    # claim evaluation against the pre-registered prediction
    c2_base_ok = m["baseline"]["wrong"] >= 6
    c2_v1_ok = m["v1"]["wrong"] <= 2
    c2_v2_le2 = m["v2"]["wrong"] <= 2
    print("\nPre-registered prediction: baseline wrong >= 6; v1 wrong <= 2")
    print(f"  baseline wrong = {m['baseline']['wrong']}  -> {verdict(c2_base_ok)}")
    print(f"  v1 wrong       = {m['v1']['wrong']}  -> {verdict(c2_v1_ok)}"
          + ("" if c2_v1_ok else "   (target missed -> revision R1 applied)"))
    print(f"  v2 wrong       = {m['v2']['wrong']}  (post-revision; <= 2 would be {verdict(c2_v2_le2)})")
    thr = 0.10
    print(f"Acceptance threshold wrong-rate on answered <= {thr:.0%}: v2 observed "
          f"{m['v2']['wrong_rate_wilson95'] and m['v2']['wrong_rate_on_answered']:.3f} "
          f"-> {verdict(m['v2']['wrong_rate_on_answered'] <= thr)} on this tiny set; "
          f"95% CI {m['v2']['wrong_rate_wilson95']} (far too wide to establish a rate)")

    # incorrect-input scenario R1 evidence
    r15 = next(p for p in per if p["id"] == 15)
    r14 = next(p for p in per if p["id"] == 14)
    print(f"\nIncorrect-input scenario (term listing): row 14 v1={r14['v1']} -> v2={r14['v2']}; "
          f"row 15 v1={r15['v1']} -> v2={r15['v2']} (expert Low)")
    return {"per_answer": per, "metrics": m, "by_style": by_style,
            "claim": {"baseline_wrong_ge_6": c2_base_ok, "v1_wrong_le_2": c2_v1_ok,
                      "v2_wrong_le_2": c2_v2_le2,
                      "v2_meets_10pct_threshold": m["v2"]["wrong_rate_on_answered"] <= thr}}


def c1_matrix():
    hdr("C1  Stakes-discrepancy moderation matrix")
    cells = {}
    expected = {("Low", 0): "Routine", ("Low", 1): "Routine", ("Low", 2): "Priority",
                ("Medium", 0): "Routine", ("Medium", 1): "Priority", ("Medium", 2): "Urgent",
                ("High", 0): "Priority", ("High", 1): "Urgent", ("High", 2): "Urgent"}
    ok_cells = 0
    print(f"{'stakes':<8}" + "".join(f"disc={d:<10}" for d in (0, 1, 2)))
    for s in matrix.STAKES:
        line = f"{s:<8}"
        for d in (0, 1, 2):
            got = matrix.priority(s, d)
            cells[f"{s}-{d}"] = got
            ok_cells += got == expected[(s, d)]
            line += f"{got:<15}"
        print(line)
    first = [matrix.priority(s, d) for s in matrix.STAKES for d in (0, 1, 2)]
    identical = all([matrix.priority(s, d) for s in matrix.STAKES for d in (0, 1, 2)] == first
                    for _ in range(1000))
    rank = matrix.PRIORITY_RANK
    mono_viol = 0
    for s_i, s in enumerate(matrix.STAKES):
        for d in (0, 1, 2):
            if d < 2 and rank[matrix.priority(s, d + 1)] < rank[matrix.priority(s, d)]:
                mono_viol += 1
            if s_i < 2 and rank[matrix.priority(matrix.STAKES[s_i + 1], d)] < rank[matrix.priority(s, d)]:
                mono_viol += 1
    bad = 0
    for args in (("Extreme", 0), ("Low", 3), ("Low", -1)):
        try:
            matrix.priority(*args)
        except ValueError:
            bad += 1
    print(f"cells correct: {ok_cells}/9 | 1,000 repeated runs identical: {identical} | "
          f"monotonicity violations: {mono_viol} | invalid inputs rejected: {bad}/3")
    ok = ok_cells == 9 and identical and mono_viol == 0 and bad == 3
    print(f"C1 prediction (9/9, identical, 0 violations): {verdict(ok)}")
    return {"cells": cells, "cells_correct": ok_cells, "repeat_identical": identical,
            "monotonicity_violations": mono_viol, "invalid_rejected": bad, "claim_pass": ok}


def c3_audit():
    hdr("C3  Hash-chained audit log: tamper tests")
    def build(content_in_chain=False, n=10):
        log = audit.AuditLog(content_in_chain=content_in_chain, rng_bytes=DetRng())
        for i in range(n):
            log.append("examiner" if i % 3 == 0 else "controller", "mark_event",
                       {"answer": f"A{i:03d}", "mark": (i * 3) % 11, "reason": ""})
        return log
    base = build()
    cp_head, cp_len = base.head()
    res = []

    def rec(tid, desc, expected, observed, extra=""):
        ok = observed.startswith(expected)
        res.append({"test": tid, "description": desc, "expected": expected,
                    "observed": observed, "pass": ok})
        print(f"{tid:<4}{desc:<58}{expected:<20}{observed:<28}{verdict(ok)} {extra}")
    print(f"{'id':<4}{'description':<58}{'expected':<20}{'observed':<28}")

    ok, bad, why = base.verify()
    rec("T1", "clean chain verifies", "Pass", "Pass" if ok else "Fail")

    l = copy.deepcopy(base)
    l.entries[4]["payload"] = "tampered"
    ok, bad, why = l.verify()
    rec("T2", "naive edit of entry 4 (no recompute)", "Detected", f"Detected at entry {bad}" if not ok else "Undetected")
    t2_obs_idx = bad

    l = copy.deepcopy(base)
    audit.privileged_rewrite(l, 4, {"answer": "A004", "mark": 10, "reason": "x"})
    ok, bad, why = l.verify()
    rec("T3", "privileged edit + recompute, no checkpoint", "Undetected", "Undetected (chain verifies)" if ok else "Detected")
    ok2, bad2, why2 = l.verify(cp_head, cp_len)
    rec("T4", "same edit against external head checkpoint", "Detected", f"Detected ({why2})" if not ok2 else "Undetected")

    l = copy.deepcopy(base)
    audit.truncate(l, 2)
    ok, _, _ = l.verify()
    rec("T5", "truncate last two entries, no checkpoint", "Undetected", "Undetected (chain verifies)" if ok else "Detected")
    ok2, _, why2 = l.verify(cp_head, cp_len)
    rec("T5b", "truncation against external checkpoint", "Detected", f"Detected ({why2})" if not ok2 else "Undetected")

    l = copy.deepcopy(base)
    l.append("examiner", "mark_event", {"answer": "A010", "mark": 9, "reason": "entered in good faith"})
    ok, _, _ = l.verify()
    rec("T6", "false original mark entered in good faith", "Chain valid", "Chain valid; truth NOT checked" if ok else "Chain invalid")

    lc = build(content_in_chain=True)
    lc.entries[2]["payload"] = "null"      # content erased where it is part of the hash
    ok, bad, _ = lc.verify()
    rec("T7a", "erase content that is hashed INTO the chain", "Chain breaks", f"Chain breaks at entry {bad}" if not ok else "Chain valid")

    l = copy.deepcopy(base)
    l.erase_content(2)
    ok, _, _ = l.verify()
    cm = l.content_matches_commitment(2)
    rec("T7b", "erase content held OUTSIDE chain (commitment kept)", "Chain valid", "Chain valid" if ok else "Chain breaks",
        extra=f"(content now unverifiable: {cm is None})")

    # T8 dictionary attack on unsalted vs salted commitments
    marks = [8, 5, 9]
    unsalted = [audit._h("unsalted", json_dumps({"mark": m})) for m in marks]
    recovered_unsalted = audit.dictionary_attack_unsalted(unsalted, range(0, 11))
    salted = [audit.commit({"mark": m}, DetRng()(8).hex()) for m in marks]
    table = {audit._h("unsalted", json_dumps({"mark": c})): c for c in range(0, 11)}
    recovered_salted = [table.get(s) for s in salted]
    rec("T8", "dictionary attack recovers low-entropy marks", "3/3 unsalted, 0/3 salted",
        f"{sum(x is not None for x in recovered_unsalted)}/3 unsalted, {sum(x is not None for x in recovered_salted)}/3 salted")

    # timing: append and verify
    big = audit.AuditLog(rng_bytes=DetRng())
    t0 = time.perf_counter()
    for i in range(10000):
        big.append("system", "event", {"i": i})
    t_append = (time.perf_counter() - t0) / 10000 * 1e6
    t0 = time.perf_counter()
    big.verify()
    t_verify = (time.perf_counter() - t0) * 1000
    c3_ok = all(r["pass"] for r in res)
    print(f"C3 prediction (all of T1..T8 as predicted): {verdict(c3_ok)}")
    return {"tests": res, "claim_pass": c3_ok}, {"append_us_per_entry": round(t_append, 2),
                                                 "verify_10000_entries_ms": round(t_verify, 1)}


def json_dumps(d):
    return json.dumps(d, sort_keys=True)


def c4_workflow(rub, rows):
    hdr("C4  Role-controlled workflow checks")
    text1 = rows[0]["text"]
    wf = ExamWorkflow(rub, "v2")
    checks = []

    def check(cid, desc, fn, expect):
        try:
            out = fn()
            observed = "ok" if expect == "ok" else "allowed"
        except Forbidden:
            observed = "Forbidden"
        except Rejected:
            observed = "Rejected"
        ok = observed == expect or (expect == "ok" and observed == "ok")
        checks.append({"check": cid, "description": desc, "expected": expect, "observed": observed, "pass": ok})
        print(f"{cid:<5}{desc:<66}{expect:<11}{observed:<11}{verdict(ok)}")
        return out if observed in ("ok", "allowed") else None

    wf.submit("A100", "stu-0042", "ex-1", text1)
    wf.submit("A101", "stu-0043", "ex-1", text1)
    wf.submit("A102", "stu-0044", "ex-2", "Contact 21CSE1234 or kumar@example.in about my answer. " + rows[4]["text"])
    wf.submit("A103", "stu-0045", "ex-1", rows[22]["text"])
    print(f"{'id':<5}{'check':<66}{'expected':<11}{'observed':<11}")
    check("A1", "assistant tries to approve a mark", lambda: wf.approve("assistant", "assistant", "A100"), "Forbidden")
    check("A2", "examiner overrides shown suggestion without reason", lambda: wf.evaluate("ex-1", "examiner", "A101", 3), "Rejected")
    prio = check("A2b", "override WITH reason succeeds (stakes High -> priority)", lambda: wf.evaluate(
        "ex-1", "examiner", "A101", 3, reason="Examiner disagrees with suggested band", stakes="High"), "ok")
    check("A3", "examiner tries to approve", lambda: wf.approve("ex-1", "examiner", "A100"), "Forbidden")
    check("A4", "moderator tries to approve", lambda: wf.approve("mod-1", "moderator", "A100"), "Forbidden")
    check("A5a", "examiner evaluates (mark 8 matches suggestion)", lambda: wf.evaluate("ex-1", "examiner", "A100", 8, stakes="Medium"), "ok")
    check("A5b", "moderator moderates", lambda: wf.moderate("mod-1", "moderator", "A100"), "ok")
    check("A5c", "controller approves (day 0)", lambda: wf.approve("ctl-1", "controller", "A100", day=0), "ok")
    check("A6", "student disputes own mark on day 3", lambda: wf.dispute("stu-0042", "student", "A100", "Q2 marked wrongly", day=3), "ok")
    check("A7", "correction WITHOUT reason", lambda: wf.correct("ctl-1", "controller", "A100", 9, ""), "Rejected")
    check("A8", "correction WITH reason", lambda: wf.correct("ctl-1", "controller", "A100", 9, "Q2 re-read; credit restored"), "ok")
    # a second answer for the late-dispute check
    wf.evaluate("ex-1", "examiner", "A103", 4, stakes="Low")
    wf.moderate("mod-1", "moderator", "A103")
    wf.approve("ctl-1", "controller", "A103", day=0)
    check("A9", "student dispute on day 9 (window is 7 days)", lambda: wf.dispute("stu-0045", "student", "A103", "late", day=9), "Rejected")
    check("A10a", "examiner views a script not assigned to them", lambda: wf.view("ex-2", "examiner", "A100"), "Forbidden")
    check("A10b", "student views another student's record", lambda: wf.view("stu-0042", "student", "A103"), "Forbidden")
    check("A10c", "student disputes another student's record", lambda: wf.dispute("stu-0042", "student", "A103", "x", day=1), "Forbidden")
    exp = {}
    out = check("A11", "redacted export by export worker", lambda: exp.update(zip(("rows", "hits"), wf.export_redacted("export_worker"))), "ok")
    leaked = any(("21CSE1234" in r["text"] or "kumar@example.in" in r["text"] or "stu-00" in r["text"]) for r in exp.get("rows", []))
    checks.append({"check": "A11b", "description": "no identifier remains in exported text", "expected": "0 leaks",
                   "observed": f"{int(leaked)} leaks ({exp.get('hits')} redactions)", "pass": not leaked})
    print(f"{'A11b':<5}{'no identifier remains in exported text':<66}{'0 leaks':<11}{int(leaked)} leaks ({exp.get('hits')} redactions)   {verdict(not leaked)}")
    check("A12", "export worker tries to approve", lambda: wf.approve("worker", "export_worker", "A100"), "Forbidden")
    hist_before = len(wf.records["A100"]["versions"])
    check("A13", "DPO erases superseded mark value (version 1)", lambda: wf.erase_superseded("dpo-1", "dpo", "A100", 1, "student erasure request"), "ok")
    ok_chain, _, _ = wf.audit.verify()
    erased_unverifiable = wf.audit.content_matches_commitment(wf.records["A100"]["versions"][0]["audit_index"]) is None
    checks.append({"check": "A13b", "description": "chain still valid; erased content unverifiable; current mark intact",
                   "expected": "valid/True/9", "observed": f"{ok_chain}/{erased_unverifiable}/{wf.current_mark('A100')}",
                   "pass": ok_chain and erased_unverifiable and wf.current_mark("A100") == 9})
    print(f"{'A13b':<5}{'chain valid; erased content unverifiable; current mark intact':<66}{'valid/True/9':<11}{ok_chain}/{erased_unverifiable}/{wf.current_mark('A100')}   {verdict(checks[-1]['pass'])}")
    hist = wf.records["A100"]["versions"]
    print(f"\nA100 history entries = {len(hist)} (before erasure note: {hist_before}), final mark = {wf.current_mark('A100')}, "
          f"state = {wf.records['A100']['state']}")
    for v in hist:
        print(f"   v{v['version']} {v['role']:<11}{v['action']:<14} mark={v['mark']!s:<5} reason={v['reason']!r}")
    print(f"A101 moderation priority after override at High stakes: {prio}")
    print("Moderation queue (highest first):", [(r['answer_id'], r['priority']) for r in wf.moderation_queue()])
    print(f"Refused attempts logged: {len(wf.denied)}")
    c4_ok = all(c["pass"] for c in checks)
    print(f"C4 prediction (all workflow checks pass): {verdict(c4_ok)}")
    return {"checks": checks, "a100_history_len_after_erasure": len(hist),
            "a100_history_len_before_erasure": hist_before,
            "a100_final_mark": wf.current_mark("A100"), "a101_priority": prio,
            "denied_attempts": len(wf.denied), "claim_pass": c4_ok}


def c5_credentials():
    hdr("C5  Retry-safe credential issue (ledger excluded; conventional signed certificate)")
    key = hashlib.sha256(b"demo-key-not-a-secret").digest()
    marks_db = {"stu-0042": {"programme": "BE-CSE", "grade": "A"}, "stu-0043": {"programme": "BE-CSE", "grade": "B"}}
    snapshot = copy.deepcopy(marks_db)
    out = []

    ver = credentials.ExternalVerifier(fail_first_n=2)
    svc = credentials.CredentialService(key, ver)
    cert = {"student": "stu-0042", **marks_db["stu-0042"]}
    r1 = svc.request_issue("issue-stu-0042", cert)
    r2 = svc.request_issue("issue-stu-0042", cert)
    f1 = (r1 == "issued" and len(svc.issued) == 1 and marks_db == snapshot and r2 == "already_issued")
    out.append({"id": "F1", "scenario": "verifier down for 2 calls, then up", "result": r1, "attempts": svc.attempt_log,
                "duplicate_request": r2, "certificates": len(svc.issued), "local_marks_unchanged": marks_db == snapshot, "pass": f1})
    print(f"F1  verifier down 2 calls: first={r1}; attempts={[a[1:] for a in svc.attempt_log]}; repeat={r2}; "
          f"certificates={len(svc.issued)}; local marks unchanged={marks_db == snapshot}  -> {verdict(f1)}")

    ver2 = credentials.ExternalVerifier(always_down=True)
    svc2 = credentials.CredentialService(key, ver2)
    r = svc2.request_issue("issue-stu-0043", {"student": "stu-0043", **marks_db["stu-0043"]})
    f2a = (r == "pending_retry" and len(svc2.pending) == 1 and len(svc2.issued) == 0 and marks_db == snapshot)
    ver2.always_down = False
    r_later = svc2.request_issue("issue-stu-0043", {"student": "stu-0043", **marks_db["stu-0043"]})
    f2 = f2a and r_later == "issued" and len(svc2.issued) == 1 and not svc2.pending
    out.append({"id": "F2", "scenario": "verifier down for whole window, recovers later", "first": r, "later": r_later,
                "local_marks_unchanged": marks_db == snapshot, "pass": f2})
    print(f"F2  verifier down for whole window: first={r} (pending kept, marks unchanged); after recovery={r_later}  -> {verdict(f2)}")

    pkg = svc.issued["issue-stu-0042"]
    f3a = svc.employer_check(pkg)
    tampered = copy.deepcopy(pkg)
    tampered["cert"]["grade"] = "O"
    f3b = svc.employer_check(tampered)
    f3 = f3a is True and f3b is False
    out.append({"id": "F3", "scenario": "employer check; tampered grade", "genuine": f3a, "tampered": f3b, "pass": f3})
    print(f"F3  employer check genuine={f3a}; tampered grade A->O accepted={f3b}  -> {verdict(f3)}")
    print("    Limitation: HMAC stand-in; a real design uses asymmetric signatures. The check proves the record is unchanged since issue, not that grade 'A' was deserved.")
    ok = all(o["pass"] for o in out)
    print(f"C5 prediction: {verdict(ok)}")
    return {"scenarios": out, "claim_pass": ok}


def c6_simulation():
    hdr("C6  Label-noise simulation (assumed noise; synthetic; NOT real marks)")
    sim = simulation.run()
    print(f"{'subject':<20}{'noise':>6}{'examiner agree':>16}{'kappa':>8}{'assistant vs ex1':>18}{'vs TRUE':>9}{'kappa>=0.6':>12}")
    for s in sim["subjects"]:
        print(f"{s['subject']:<20}{s['assumed_noise']:>6.2f}{s['examiner_agreement']:>16.3f}{s['examiner_kappa']:>8.3f}"
              f"{s['assistant_vs_examiner1']:>18.3f}{s['assistant_vs_true']:>9.3f}{str(s['passes_kappa_gate']):>12}")
    db, os_ = sim["subjects"]
    ok = db["examiner_kappa"] >= 0.7 and os_["examiner_kappa"] < 0.4
    print("Note: 'vs TRUE' is 1.000 by construction (text is generated from rubric terms) - not performance evidence.")
    print(f"C6 prediction (DB kappa >= 0.7, OS kappa < 0.4): {verdict(ok)}")
    sim["claim_pass"] = ok
    return sim


def selection_section():
    hdr("Task 2  Weighted decision matrix and sensitivity")
    base = selection.table(selection.S0, selection.W0)
    print("Weights (%):  " + " | ".join(f"{k} {v}" for k, v in list(selection.W0.items())[:4]))
    print("               " + " | ".join(f"{k} {v}" for k, v in list(selection.W0.items())[4:]))
    print(f"{'criterion':<24}" + "".join(f"{a:>5}" for a in selection.S0))
    for c in selection.CRITERIA:
        print(f"{c:<24}" + "".join(f"{selection.S0[a][c]:>5}" for a in selection.S0))
    print(f"{'WEIGHTED (out of 5)':<24}" + "".join(f"{base[a]:>5.2f}" for a in base))
    sens = selection.sensitivity()
    print("\nSensitivity:")
    for name, t in sens.items():
        best = max(t, key=t.get)
        print(f"  {name:<52}" + "  ".join(f"{a}={t[a]:.2f}" for a in t) + f"   best={best}")
    sw = selection.sweep("Usefulness")
    sw_st = selection.sweep("Shared-trust need", selection.with_overrides(selection.S0, selection._S3))
    sw_u2 = selection.sweep("Usefulness", selection.with_overrides(selection.S0, selection._S2))
    be = selection.break_evens()
    print("\nBreak-even weight at which an alternative first beats A (others scaled; None = never within 0-90%):")
    for k, v in be.items():
        print(f"  {k:<40}{v}")
    rev = selection.revised()
    print("\nTask 6 revised scores:")
    for c in selection.CRITERIA:
        print(f"  {c:<24}" + "".join(f"{rev['scores'][a][c]:>5}" for a in rev["scores"]))
    print("  weighted, original weights:", rev["original_weights"])
    print("  weighted, revised weights :", rev["revised_weights"])
    print("  revised weights (%):", " | ".join(f"{k} {v}" for k, v in selection.W_REVISED.items()))
    return {"weights": selection.W0, "scores": selection.S0, "base": base,
            "sensitivity": sens, "break_even": be,
            "sweep_usefulness_base": {"weights": sw["weights"], "curve": sw["curve"]},
            "sweep_usefulness_labels": {"weights": sw_u2["weights"], "curve": sw_u2["curve"]},
            "sweep_trust_committed": {"weights": sw_st["weights"], "curve": sw_st["curve"]},
            "revised": {"scores": rev["scores"], "original_weights": rev["original_weights"],
                        "revised_weights": rev["revised_weights"], "weights": selection.W_REVISED}}


def resources_section():
    hdr("Task 5  Resource and cost estimates (assumption-linked; only rule time is measured)")
    est = resources.estimates(None)
    print(f"answers/cycle={est['answers_per_cycle']:,}  answers/year={est['answers_per_year']:,}  per-answer storage={est['per_answer_kb']} KB")
    print(f"rule CPU (planning 1 ms/answer) = {est['rule_cpu_s_cycle_planning']} CPU-s/cycle; storage = {est['storage_mb_cycle']} MB/cycle, {est['storage_mb_year']} MB/year")
    print(f"budget per cycle: original {est['budget_original']} CPU-s, halved {est['budget_halved']} CPU-s")
    print(f"{'alt':<4}{'CPU-s/cycle':>12}{'storage MB/yr':>15}{'label h/round':>15}{'fixed Rs/yr':>13}{'gov h/yr':>10}{'fits orig':>10}{'fits half':>10}")
    for a, v in est["alternatives"].items():
        print(f"{a:<4}{v['cpu_s_cycle']:>12.1f}{v['storage_mb_year']:>15.1f}{v['labelling_hours_round']:>15}{v['fixed_rs_year']:>13,}{v['governance_hours_year']:>10}"
              f"{str(v['fits_original_budget']):>10}{str(v['fits_halved_budget']):>10}")
    print("All values except the measured rule time are ESTIMATES from the stated assumptions. No energy or carbon claim is made.")
    return est


def timing_section(rub, rows):
    hdr("Measured timing (single machine; NOT a production benchmark)")
    texts = [r["text"] for r in rows]
    runs = []
    for _ in range(5):
        t0 = time.perf_counter()
        for _ in range(500):
            for t in texts:
                rubric.assist(t, rub, "v2")
        runs.append((time.perf_counter() - t0) / (500 * len(texts)) * 1000)
    ms = statistics.median(runs)
    print(f"rule evaluation (v2): median {ms:.4f} ms per answer over 5 runs of {500*len(texts):,} evaluations")
    return {"rule_eval_ms_per_answer_median": round(ms, 4), "runs_ms": [round(x, 4) for x in runs],
            "python": sys.version.split()[0], "platform": platform.platform(),
            "note": "single-machine figure; not a production benchmark"}


def main():
    print("CSA10 Assignment 5 - Responsible technology adoption demonstrator")
    print(f"seed={SEED} | python {sys.version.split()[0]} | standard library only")
    print("Trained ML and Blockchain are evaluated as options; neither is implemented here.")
    rub = rubric.load_rubric()
    rows = rubric.load_answers()
    results = {"seed": SEED}
    results["C2"] = c2_assistant(rub, rows)
    results["C1"] = c1_matrix()
    c3, audit_timing = c3_audit()
    results["C3"] = c3
    results["C4"] = c4_workflow(rub, rows)
    results["C5"] = c5_credentials()
    results["C6"] = c6_simulation()
    results["selection"] = selection_section()
    results["resources"] = resources_section()
    timing = timing_section(rub, rows)
    timing.update(audit_timing)
    est_t = resources.estimates(timing["rule_eval_ms_per_answer_median"])
    timing["rule_cpu_s_cycle_measured"] = est_t["rule_cpu_s_cycle_measured"]
    print(f"audit append: {audit_timing['append_us_per_entry']} us/entry; verify 10,000 entries: {audit_timing['verify_10000_entries_ms']} ms")
    print(f"measured rule CPU for {est_t['answers_per_cycle']:,} answers = {est_t['rule_cpu_s_cycle_measured']} CPU-s (planning figure uses 1 ms/answer)")

    hdr("SUMMARY OF PRE-REGISTERED CLAIMS")
    claims = {
        "C1 deterministic matrix": results["C1"]["claim_pass"],
        "C2a baseline wrong >= 6": results["C2"]["claim"]["baseline_wrong_ge_6"],
        "C2b v1 wrong <= 2 (target)": results["C2"]["claim"]["v1_wrong_le_2"],
        "C2c v2 wrong <= 2 (post-revision)": results["C2"]["claim"]["v2_wrong_le_2"],
        "C2d v2 meets 10% wrong-rate threshold": results["C2"]["claim"]["v2_meets_10pct_threshold"],
        "C3 audit tamper behaviour": results["C3"]["claim_pass"],
        "C4 workflow authorisation": results["C4"]["claim_pass"],
        "C5 retry-safe credential issue": results["C5"]["claim_pass"],
        "C6 label noise limits agreement": results["C6"]["claim_pass"],
    }
    for k, v in claims.items():
        print(f"  {k:<42}{verdict(v)}")
    results["claims_summary"] = claims

    (OUT / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    (OUT / "timing.json").write_text(json.dumps(timing, indent=2, sort_keys=True), encoding="utf-8")
    print("\nWrote results/results.json and results/timing.json")


if __name__ == "__main__":
    main()
