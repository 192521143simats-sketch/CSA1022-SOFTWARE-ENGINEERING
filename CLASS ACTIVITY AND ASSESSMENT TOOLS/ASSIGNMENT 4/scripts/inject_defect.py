"""Controlled defect injection (mutation testing by hand).
For each named defect: copy the project to a temp dir, apply ONE edit, run the suite, record
the failing tests, then run the untouched copy again. Usage: python scripts/inject_defect.py [name ...]"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFECTS = {
    "D1-threshold-gte": ("campus/rules.py",
        "return to_decimal(value) > to_decimal(limit)", "return to_decimal(value) >= to_decimal(limit)",
        "sensor threshold boundary: 28.0 wrongly breaches"),
    "D2-matrix-high-high-M2": ("campus/rules.py",
        '("High", "High"): "M1"', '("High", "High"): "M2"',
        "triage: High/High returns M2 instead of M1"),
    "D3-overlap-ignores-approved": ("campus/services.py",
        "status IN ('Pending','Approved')", "status IN ('Pending')",
        "double booking: an overlapping request is accepted when the earlier one is Approved"),
    "D4-restricted-approval-unchecked": ("campus/services.py",
        'if r["restricted"]:\n            _need(role, "booking:approve_restricted")', 'if False:\n            pass',
        "an approver may approve a restricted laboratory booking"),
    "D5-sensor-duplicate-not-detected": ("campus/services.py",
        "        if old:\n            return {\"breach\": True, \"duplicate\": True, \"ticket_id\": old[\"id\"]}, 200\n",
        "", "retried sensor event is not recognised -> duplicate ticket path"),
    "D7-calendar-failure-marked-synced": ("campus/integration.py",
        "        return status\n    with tx(db):", "        remote = 'ASSUMED'\n    with tx(db):",
        "release 2.0: a failed calendar/tracker call is recorded as Synced"),
    "D8-campus-policy-ignored": ("campus/policy.py",
        'mine = [p for p in policies if p["campus_code"] == (campus or DEFAULT_CAMPUS)]',
        'mine = [p for p in policies if p["campus_code"] == DEFAULT_CAMPUS]',
        "release 2.0: every campus gets the MAIN policy (NORTH 120-minute limit not enforced)"),
    "D9-backfill-skipped": ("migrations/002_expand_campus_policy.sql",
        "UPDATE bookings SET campus_code='MAIN', policy_version=1;", "",
        "migration 002: legacy bookings are not backfilled with a policy version"),
    "D10-retry-unbounded": ("campus/integration.py",
        "    if attempts >= MAX_ATTEMPTS:\n        return None", "    if False:\n        return None",
        "release 2.0: retries never stop (no operator escalation)"),
}



def run_pytest(cwd):
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line"],
                       cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main(names):
    out = []
    for name in names or DEFECTS:
        rel, old, new, desc = DEFECTS[name]
        with tempfile.TemporaryDirectory() as tmp:
            for item in ("campus", "migrations", "tests", "scripts", "pytest.ini"):
                src = os.path.join(ROOT, item)
                (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(tmp, item))
            f = os.path.join(tmp, rel)
            text = open(f).read()
            assert text.count(old) == 1, "mutation anchor not unique/found for %s" % name
            open(f, "w").write(text.replace(old, new))
            rc_bad, log_bad = run_pytest(tmp)
        with tempfile.TemporaryDirectory() as tmp:
            for item in ("campus", "migrations", "tests", "scripts", "pytest.ini"):
                src = os.path.join(ROOT, item)
                (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(tmp, item))
            rc_ok, log_ok = run_pytest(tmp)
        assert rc_ok == 0, "harness baseline (unmodified copy) must pass before a result is meaningful:\n" + log_ok[-400:]
        failing = sorted(set(re.findall(r"FAILED tests/\S+?::(test_\w+)", log_bad)))
        summary = log_bad.strip().splitlines()[-1]
        out.append("=" * 78 + "\nDEFECT %s\n  %s\n  file: %s\n  injected-run exit=%s  | %s\n  failing tests: %s\n"
                   "  after correction exit=%s | %s\n" % (name, desc, rel, rc_bad, summary,
                   ", ".join(failing) or "NONE (defect escaped!)", rc_ok, log_ok.strip().splitlines()[-1]))
        out.append("--- raw output with defect (failures only) ---\n" +
                   "\n".join(l for l in log_bad.splitlines() if "FAILED" in l or "assert" in l.lower()
                             or "Error" in l)[:2500] + "\n")
    text = "\n".join(out)
    print(text)
    return text


if __name__ == "__main__":
    main(sys.argv[1:])
