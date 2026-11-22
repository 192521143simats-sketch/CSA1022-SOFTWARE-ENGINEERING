#!/usr/bin/env python3
"""Render real program output (results/run_log.txt, results/unit_tests.txt) as HD terminal screenshots.
Text is taken verbatim from the logs; nothing is typed by hand."""
import html, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "screenshots"; OUT.mkdir(exist_ok=True)
log = (ROOT / "results" / "run_log.txt").read_text()
ut = (ROOT / "results" / "unit_tests.txt").read_text()

def section(start, end=None):
    i = log.index(start)
    i = log.rfind("=" * 78, 0, i)
    j = len(log)
    if end:
        k = log.index(end)
        j = log.rfind("=" * 78, 0, k)
    return log[i:j].strip("\n")

SHOTS = {
 "shot01_C2_assistant_vs_baseline": ("python3 run_demonstrator.py   # claim C2", section("C2  Rule assistant", "C1  Stakes")),
 "shot02_C1_matrix": ("python3 run_demonstrator.py   # claim C1", section("C1  Stakes", "C3  Hash")),
 "shot03_C3_audit_tamper": ("python3 run_demonstrator.py   # claim C3", section("C3  Hash", "C4  Role")),
 "shot04_C4_workflow": ("python3 run_demonstrator.py   # claim C4", section("C4  Role", "C5  Retry")),
 "shot05_C5_C6": ("python3 run_demonstrator.py   # claims C5, C6", section("C5  Retry", "Task 2  Weighted")),
 "shot06_selection_sensitivity": ("python3 run_demonstrator.py   # Task 2", section("Task 2  Weighted", "Task 5  Resource")),
 "shot07_resources_summary": ("python3 run_demonstrator.py   # Task 5 + summary", section("Task 5  Resource")),
 "shot08_unit_tests": ("python3 -m unittest discover -s tests -v", "\n".join(l for l in ut.splitlines() if "... ok" not in l or "test_" not in l) + "\n(" + str(ut.count("... ok")) + " individual tests listed as ok in results/unit_tests.txt)"),
}

def colour(line):
    l = html.escape(line)
    l = re.sub(r"\bPASS\b", '<b class="p">PASS</b>', l)
    l = re.sub(r"\bFAIL\b", '<b class="f">FAIL</b>', l)
    l = re.sub(r"^(=+)$", r'<span class="d">\1</span>', l)
    l = re.sub(r"(\*)", r'<b class="f">*</b>', l)
    l = re.sub(r"^(OK)$", r'<b class="p">OK</b>', l)
    return l

PAGE = """<!doctype html><html><head><meta charset=utf-8><style>
body{{margin:0;background:#e9edf3;padding:28px}}
.win{{display:inline-block;background:#0f1722;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.28);overflow:hidden;min-width:900px}}
.bar{{background:#1c2736;padding:11px 16px;display:flex;align-items:center;gap:8px}}
.dot{{width:12px;height:12px;border-radius:50%}}
.t{{color:#9fb0c6;font:13px 'DejaVu Sans',sans-serif;margin-left:12px}}
pre{{margin:0;padding:18px 22px 22px;color:#d6e2f0;font:15px/1.38 'DejaVu Sans Mono',monospace;white-space:pre}}
.cmd{{color:#7dd3fc}} .p{{color:#4ade80}} .f{{color:#f87171}} .d{{color:#3b4a5f}}
</style></head><body><div class=win id=w><div class=bar><span class=dot style="background:#ff5f57"></span><span class=dot style="background:#febc2e"></span><span class=dot style="background:#28c840"></span><span class=t>responsible-tech-demonstrator — terminal</span></div>
<pre><span class=cmd>$ {cmd}</span>
{body}</pre></div></body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, (cmd, body) in SHOTS.items():
        pg = b.new_page(device_scale_factor=2, viewport={"width": 1900, "height": 900})
        pg.set_content(PAGE.format(cmd=html.escape(cmd), body="\n".join(colour(l) for l in body.splitlines())))
        pg.locator("#w").screenshot(path=str(OUT / f"{name}.png"))
        print("wrote", name)
    b.close()
