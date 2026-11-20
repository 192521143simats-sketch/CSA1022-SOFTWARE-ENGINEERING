"""Tiny repository secret scan used by the local runner (CI also runs gitleaks).
Scope: tracked files only (git ls-files), hard-coded assignments to secret-like names,
excluding tests. NOT a complete scanner: no entropy checks, no git-history scan."""
import pathlib
import re
import subprocess
import sys

PAT = re.compile(r"(?i)(secret|password|passwd|token|api[_-]?key)\s*[:=]\s*['\"][^'\"\s]{6,}['\"]")
ALLOW = ("os.environ", "${{", "${", "get(")
SKIP_PREFIX = ("tests/", "evidence/")


def find(text):
    """Return [(line_no, line)] of suspicious assignments in a text."""
    return [(n, l.strip()) for n, l in enumerate(text.splitlines(), 1)
            if PAT.search(l) and not any(a in l for a in ALLOW)]


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    files = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True).stdout.split()
    bad = []
    for rel in files:
        if rel.startswith(SKIP_PREFIX) or rel.endswith("secret_scan.py"):
            continue
        p = root / rel
        if p.suffix in {".png", ".docx", ".pdf", ".db", ".zip"} or not p.is_file():
            continue
        for n, line in find(p.read_text(errors="ignore")):
            bad.append("%s:%d: %s" % (rel, n, line[:80]))
    print("secret-scan: %d tracked file(s) scanned, %d finding(s)" % (len(files), len(bad)))
    print("\n".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
