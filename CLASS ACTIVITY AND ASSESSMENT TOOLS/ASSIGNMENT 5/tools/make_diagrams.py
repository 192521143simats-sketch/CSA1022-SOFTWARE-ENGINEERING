#!/usr/bin/env python3
"""Architecture diagrams drawn with matplotlib (vector geometry, rendered at 250 dpi)."""
from pathlib import Path

from fig_common import *  # noqa

FIG = Path(__file__).resolve().parent.parent / "figures"
FIG.mkdir(exist_ok=True)


# ============================================================ stakeholder map
def fig_stakeholders():
    fig, ax = canvas(200, 100)
    ax.text(100, 96, "Stakeholder map: who needs what from the platform (simulated stakeholder responses)",
            ha="center", fontsize=15, fontweight="bold")
    box(ax, 72, 38, 56, 24, "Examination &\nCredential Platform\n\nrubric-rule assistance + human\nevaluation, moderation, approval,\nrevaluation, credential issue",
        fc=BLUE_L, ec=BLUE, lw=2.2, fs=10.5, bold=False)
    internal = [
        ("Students", "Correct wrongly recorded marks;\nrevaluation route; privacy", 6, 70, TEAL),
        ("Examiners", "Visible rubric evidence;\neasy, recorded override", 6, 46, TEAL),
        ("Moderators", "Sample ordered by risk,\nnot random only", 6, 22, TEAL),
        ("Controller of examinations", "Sole approval authority;\ncorrection with reason", 76, 76, AMBER),
        ("Administrators / DPO", "Minimum personal data;\nerasure and retention rules", 76, 8, AMBER),
        ("Department heads", "Subject-level consistency\nreports (aggregates only)", 144, 70, TEAL),
        ("Partner institutions / employers", "Verifiable certificates\n(no marks, no identities)", 144, 38, VIOLET),
        ("Operations staff", "Low overhead, simple\ndeployment and upkeep", 144, 8, TEAL),
    ]
    for name, need, x, y, c in internal:
        box(ax, x, y, 50, 16, "", fc="#fff", ec=c, lw=1.8)
        ax.text(x + 25, y + 12.2, name, ha="center", fontsize=10.5, fontweight="bold", color=c)
        ax.text(x + 25, y + 5.2, need, ha="center", va="center", fontsize=8.6, color=INK, linespacing=1.3)
        cx = x + (50 if x < 70 else 0 if x > 140 else 25)
        cy = y + (8 if x != 76 else (0 if y > 50 else 16))
        tx = 72 if x < 70 else 128 if x > 140 else 100
        ty = 50 if x != 76 else (62 if y > 50 else 38)
        route(ax, [(cx, cy), (tx, ty)], color=c, lw=1.3, both=True, head=9)
    ax.text(100, 2, "Teal = internal users   Amber = governance owners   Violet = external verifier.   "
            "Responses are simulated and labelled as such; they are not interview transcripts.",
            ha="center", fontsize=9, color=MUTED)
    save(fig, FIG / "fig01_stakeholder_map.png")


# ============================================================ component diagram
def fig_components():
    fig, ax = canvas(200, 112)
    ax.text(100, 108, "Selected blueprint: component diagram (Alternative A: rubric rules + human evaluation, conventional certificates)",
            ha="center", fontsize=14.5, fontweight="bold")
    # layer bands
    for y, h, t in [(84, 20, "PRESENTATION  (untrusted clients)"), (64, 16, "ACCESS CONTROL"),
                    (30, 30, "APPLICATION SERVICES"), (4, 22, "DATA STORES")]:
        ax.add_patch(Rectangle((2, y), 158, h, fc="#f8fafc", ec=GRID, lw=1.2, zorder=0))
        ax.text(3.2, y + h - 1.2, t, fontsize=8.5, color=MUTED, va="top", fontweight="bold")
    for i, (n, x) in enumerate([("Student\nbrowser", 6), ("Examiner\nbrowser", 42), ("Moderator\nbrowser", 78), ("Controller / admin\nbrowser", 114)]):
        box(ax, x, 86, 32, 12, n, fc=TEAL_L, ec=TEAL, fs=9.5, bold=True)
        route(ax, [(x + 16, 86), (x + 16, 77)], color=TEAL, lw=1.4)
    box(ax, 6, 66, 150, 11, "API gateway:  authentication  |  role-based access control (least privilege)  |  input validation  |  rate limiting",
        fc=BLUE_L, ec=BLUE, fs=10, bold=True)
    svc = [("Evaluation service\nRubric-rule assistant\n(deterministic, NOT ML)\nsuggests band + matched terms;\nabstains to Manual Review", 6, BLUE_L, BLUE),
           ("Workflow service\nevaluate > moderate > approve\n> dispute > correct\nreasons mandatory;\nversioned history", 38, BLUE_L, BLUE),
           ("Audit service\nhash chain of salted\ncommitments; no names,\nno answer text", 70, BLUE_L, BLUE),
           ("Redaction / export worker\nremoves identifiers;\nno approval rights", 102, AMBER_L, AMBER),
           ("Credential service\nsigned certificate;\nidempotent retry queue", 134, VIOLET_L, VIOLET)]
    for t, x, fc, ec in svc:
        box(ax, x, 33, 29, 23, t, fc=fc, ec=ec, fs=7.8, bold=False)
        route(ax, [(x + 14.5, 66), (x + 14.5, 56)], color=BLUE, lw=1.2, both=True, head=8)
    stores = [("Marks database (S)\nversioned corrections", 6, RED_L, RED),
              ("Restricted content store (S)\nanswer text, salts", 38, RED_L, RED),
              ("Audit chain store\ncommitments + hashes", 70, SLATE_L, SLATE),
              ("Redacted evaluation samples\nno identifiers", 102, AMBER_L, AMBER),
              ("Certificate register\nsigned certificates", 134, VIOLET_L, VIOLET)]
    for t, x, fc, ec in stores:
        box(ax, x, 6, 29, 14, t, fc=fc, ec=ec, fs=8, bold=True, rad=0.6)
    for x in (6, 38, 70, 102, 134):
        route(ax, [(x + 14.5, 33), (x + 14.5, 20)], color=INK, lw=1.2, both=True, head=8)
    # side panel
    ax.add_patch(Rectangle((164, 4), 34, 100, fc="#fff", ec=SLATE, lw=1.4, ls=(0, (6, 4))))
    ax.text(181, 101, "OUTSIDE THE PLATFORM", ha="center", fontsize=8.5, fontweight="bold", color=SLATE)
    box(ax, 166, 82, 30, 15, "Internal audit office\nstores daily head-hash +\nentry count (checkpoint)", fc=GREEN_L, ec=GREEN, fs=7.8, bold=True)
    box(ax, 166, 44, 30, 12, "Public verification page\nfingerprint check only;\nno marks or identities", fc=VIOLET_L, ec=VIOLET, fs=7.8, bold=True)
    box(ax, 166, 62, 30, 12, "Employer / partner\nverifier", fc="#fff", ec=VIOLET, fs=8, bold=True)
    route(ax, [(181, 62), (181, 56)], color=VIOLET, lw=1.3, both=True, head=8)
    box(ax, 166, 24, 30, 15, "Trained ML scorer: OPTION\noffline sandbox only; gated\nby labels (kappa >= 0.6)", fc="#fff", ec=SLATE, fs=7.6, ls="--", color=MUTED)
    box(ax, 166, 6, 30, 12, "Blockchain ledger:\nEXCLUDED (no independent\nparticipants)", fc="#fff", ec=RED, fs=7.6, ls="--", color=RED)
    ax.plot([167, 195], [6, 18], color=RED, lw=1.0, alpha=.25, zorder=3.5); ax.plot([167, 195], [18, 6], color=RED, lw=1.0, alpha=.25, zorder=3.5)
    route(ax, [(99, 54), (100.5, 54), (100.5, 61), (161, 61), (161, 90), (166, 90)], color=GREEN, lw=1.4, ls="--")
    label(ax, 130, 61, "daily head-hash (export)", fs=7.5, color=GREEN, bold=True)
    route(ax, [(163, 50), (166, 50)], color=VIOLET, lw=1.5)
    label(ax, 164.5, 58.5, "fingerprint\nonly", fs=6.6, color=VIOLET, bold=True)
    ax.text(81, 1.2, "(S) = sensitive data: names, register numbers, answer text, marks.   Solid = runtime calls.   Dashed = export or option.",
            ha="center", fontsize=8.8, color=MUTED)
    save(fig, FIG / "fig02_component_diagram.png")


# ============================================================ DFD with trust boundaries
def fig_dfd():
    fig, ax = canvas(220, 124, size=(17, 9.6))
    ax.text(110, 120, "Data-flow diagram with trust boundaries and sensitive data (selected blueprint)", ha="center",
            fontsize=15, fontweight="bold")
    zone(ax, 2, 14, 36, 98, "Z1  Untrusted user zone", ec=TEAL)
    zone(ax, 44, 8, 94, 104, "Z2  Institution trust zone", ec=BLUE)
    zone(ax, 146, 80, 72, 32, "Z3  Restricted evaluation zone", ec=AMBER)
    zone(ax, 146, 46, 72, 28, "Z4  Independent audit zone", ec=GREEN)
    zone(ax, 146, 8, 72, 32, "Z5  Public verification zone", ec=VIOLET)
    # entities
    ents = [("Student", 96), ("Examiner", 80), ("Moderator", 64), ("Controller /\nadministrator", 48), ("Department head\n(aggregates)", 32)]
    for n, y in ents:
        box(ax, 5, y, 30, 11, n, fc=TEAL_L, ec=TEAL, fs=9, bold=True)
    for _, y in ents:
        ax.plot([35, 42], [y + 5.5, y + 5.5], color=TEAL, lw=1.4, zorder=5)
    ax.plot([42, 42], [37.5, 101.5], color=TEAL, lw=1.4, zorder=5)
    route(ax, [(42, 71), (48, 71)], color=TEAL, lw=1.6, both=True)
    # processes
    def proc(x, y, w, h, t, fc=BLUE_L, ec=BLUE):
        box(ax, x, y, w, h, t, fc=fc, ec=ec, fs=8.2, bold=True, rad=3)
    def store(x, y, w, h, t, sens=False):
        c = RED if sens else SLATE
        ax.add_patch(Rectangle((x, y), w, h, fc=RED_L if sens else SLATE_L, ec=c, lw=1.6, zorder=3))
        ax.plot([x + 2.5, x + 2.5], [y, y + h], color=c, lw=1.2, zorder=4)
        ax.text(x + w / 2 + 1, y + h / 2, t, ha="center", va="center", fontsize=8, fontweight="bold", color=c, zorder=5)
    proc(48, 62, 26, 18, "P1\nAPI gateway\nauthenticate, authorise,\nvalidate input")
    proc(80, 90, 26, 16, "P2\nRubric-rule assistant\n(deterministic)")
    proc(80, 62, 26, 18, "P3\nWorkflow service\nevaluate, moderate,\napprove, dispute, correct")
    proc(80, 36, 26, 14, "P4\nAudit append\nsalted commitment")
    proc(48, 22, 26, 16, "P5\nCredential issue\nsigned, retry-safe", fc=VIOLET_L, ec=VIOLET)
    store(112, 62, 22, 18, "D1  Marks DB (S)\nversioned", True)
    store(112, 90, 22, 16, "D2  Restricted\ncontent (S)", True)
    store(112, 36, 22, 14, "D3  Audit chain\n(commitments)")
    proc(152, 86, 28, 18, "P6\nRedaction worker\nremoves identifiers", fc=AMBER_L, ec=AMBER)
    store(188, 86, 26, 18, "D4  Redacted\nsamples")
    store(152, 52, 62, 16, "D5  Daily head-hash + entry count\n(internal audit office)")
    proc(152, 14, 28, 18, "Public verification\npage\nfingerprint only", fc=VIOLET_L, ec=VIOLET)
    box(ax, 188, 14, 26, 18, "Employer /\npartner verifier", fc="#fff", ec=VIOLET, fs=8.5, bold=True)
    # flows
    route(ax, [(74, 71), (80, 71)], lw=1.4); tag(ax, 77, 74.2, "2")
    route(ax, [(88, 80), (88, 90)], lw=1.4); tag(ax, 85, 85, "3")
    route(ax, [(98, 90), (98, 80)], lw=1.4); tag(ax, 101, 85, "4")
    route(ax, [(112, 98), (106, 98)], lw=1.4, color=RED); tag(ax, 109, 101, "5", fc=RED)
    route(ax, [(106, 70), (112, 70)], lw=1.4, color=RED, both=True); tag(ax, 109, 73, "6", fc=RED)
    route(ax, [(106, 77), (109, 77), (109, 94), (112, 94)], lw=1.4, color=RED); tag(ax, 109.0, 85, "7", fc=RED)
    route(ax, [(93, 62), (93, 50)], lw=1.4); tag(ax, 96, 56, "8")
    route(ax, [(106, 43), (112, 43)], lw=1.4); tag(ax, 109, 46, "9")
    route(ax, [(82, 62), (82, 58), (61, 58), (61, 38)], lw=1.4, color=VIOLET); tag(ax, 70, 58, "13", fc=VIOLET, r=2.0, fs=7)
    route(ax, [(134, 98), (152, 98)], lw=1.4, color=RED); tag(ax, 143, 101, "11", fc=RED, r=2.0, fs=7)
    route(ax, [(180, 95), (188, 95)], lw=1.4); tag(ax, 184, 98, "12")
    route(ax, [(134, 40), (141, 40), (141, 60), (152, 60)], lw=1.4, color=GREEN); tag(ax, 141, 50, "10", fc=GREEN, r=2.0, fs=7)
    route(ax, [(61, 22), (61, 11), (166, 11), (166, 14)], lw=1.4, color=VIOLET); tag(ax, 110, 11, "14", fc=VIOLET, r=2.0, fs=7)
    route(ax, [(180, 23), (188, 23)], lw=1.4, color=VIOLET, both=True); tag(ax, 184, 26, "15", fc=VIOLET, r=2.0, fs=7)
    tag(ax, 42, 84, "1")
    # boundaries B1..B5
    for x, y, t in [(40.5, 60, "B1"), (138, 98, "B3"), (146, 11, "B5"), (138, 58, "B4"), (61, 8, "B2")]:
        tag(ax, x, y, t, fc="#c2410c", r=2.2, fs=7)
    # legend
    ax.add_patch(Rectangle((2, 1), 216, 6, fc="#fff", ec=GRID, lw=1))
    ax.text(4, 4, "Boundaries:  B1 browser > API   B2 institution egress to public network   B3 database > export worker   B4 audit log > independent checkpoint   B5 public zone entry.        "
            "Red = sensitive (S): names/register numbers, answer text, marks.    Numbers = flows F1-F15 (see report table).",
            fontsize=7.6, va="center", color=INK)
    save(fig, FIG / "fig03_data_flow_diagram.png")


# ============================================================ governance workflow (swimlane)
def fig_workflow():
    fig, ax = canvas(220, 112, size=(17, 8.6))
    ax.text(110, 108, "Governance workflow: examiner review, recorded override, correction and student challenge", ha="center",
            fontsize=15, fontweight="bold")
    lanes = ["Student", "Examiner", "Assistant\n(system)", "Moderator", "Controller", "Revaluation\ncommittee", "Data protection\nofficer"]
    lc = [TEAL, BLUE, SLATE, BLUE, AMBER, VIOLET, RED]
    lh, top = 13, 100
    ly = {}
    for i, (n, c) in enumerate(zip(lanes, lc)):
        y = top - (i + 1) * lh
        ly[n] = y
        ax.add_patch(Rectangle((2, y), 216, lh, fc="#fbfcfe" if i % 2 == 0 else "#f3f6fa", ec=GRID, lw=1, zorder=0))
        ax.add_patch(Rectangle((2, y), 21, lh, fc=c, ec="#fff", lw=1, zorder=1, alpha=.92))
        ax.text(12.5, y + lh / 2, n, ha="center", va="center", fontsize=8.6, color="#fff", fontweight="bold", zorder=2)
    cx = lambda i: 36 + 23 * i
    def step(i, lane, text, num, c=INK, fc="#fff"):
        y = ly[lane] + 1.6
        box(ax, cx(i) - 10.5, y, 21, lh - 3.2, text, fc=fc, ec=c, fs=6.9, bold=False, rad=1.0)
        tag(ax, cx(i) - 10.5, y + lh - 3.2, str(num), fc=c, r=1.5, fs=7)
        return (cx(i), y, lh - 3.2)
    def mid(i, lane):
        return cx(i), ly[lane] + lh / 2
    step(0, "Student", "Submits answer\nscript (pseudonymous id)", 1, TEAL)
    step(1, "Examiner", "Reads answer, records\nPROVISIONAL mark\n(blind to suggestion)", 2, BLUE)
    step(2, "Assistant\n(system)", "Reveals suggested band\n+ matched terms; or\nManual Review", 3, SLATE, SLATE_L)
    step(3, "Examiner", "Accepts, or overrides\n(reason mandatory)", 4, BLUE)
    step(4, "Moderator", "Moderates queue ordered\nby stakes x discrepancy", 5, BLUE)
    step(5, "Controller", "APPROVES (only role\nthat can approve)", 6, AMBER, AMBER_L)
    step(6, "Student", "May dispute within\n7 days, with reason", 7, TEAL)
    step(7, "Controller", "Corrects with reason:\nnew version, history kept", 8, AMBER)
    step(7, "Revaluation\ncommittee", "If contested: decides\nthe dispute", 9, VIOLET)
    step(7, "Data protection\nofficer", "Erases superseded\nsensitive value; keeps\ncommitment + metadata", 10, RED)
    R = lambda i, lane: (cx(i) + 10.5, mid(i, lane)[1])
    L = lambda i, lane: (cx(i) - 10.5, mid(i, lane)[1])
    B = lambda i, lane: (cx(i), ly[lane] + 1.6)
    T = lambda i, lane: (cx(i), ly[lane] + lh - 1.6)
    route(ax, [R(0, "Student"), (cx(1), mid(0, "Student")[1]), T(1, "Examiner")], lw=1.6)
    route(ax, [R(1, "Examiner"), (cx(2), mid(1, "Examiner")[1]), T(2, "Assistant\n(system)")], lw=1.6)
    route(ax, [R(2, "Assistant\n(system)"), (cx(3), mid(2, "Assistant\n(system)")[1]), B(3, "Examiner")], lw=1.6)
    route(ax, [R(3, "Examiner"), (cx(4), mid(3, "Examiner")[1]), T(4, "Moderator")], lw=1.6)
    route(ax, [R(4, "Moderator"), (cx(5), mid(4, "Moderator")[1]), T(5, "Controller")], lw=1.6)
    route(ax, [R(5, "Controller"), (cx(6), mid(5, "Controller")[1]), B(6, "Student")], lw=1.6)
    route(ax, [(cx(6) + 10.5, mid(6, "Student")[1]), (cx(7), mid(6, "Student")[1]), T(7, "Controller")], lw=1.6)
    route(ax, [(cx(7) + 10.5, mid(7, "Controller")[1]), (cx(7) + 13, mid(7, "Controller")[1]), (cx(7) + 13, mid(7, "Revaluation\ncommittee")[1]), (cx(7) + 10.5, mid(7, "Revaluation\ncommittee")[1])], lw=1.4, color=VIOLET)
    route(ax, [(cx(7) - 13, ly["Controller"] + 4), (cx(7) - 13, ly["Data protection\nofficer"] + 8), (cx(7) - 10.5, ly["Data protection\nofficer"] + 8)], lw=1.3, color=RED, ls="--")
    # callouts
    box(ax, 26, 63.5, 42, 8, "RULE: the assistant cannot approve,\npublish or change a mark", fc=RED_L, ec=RED, fs=7.8, bold=True, color=RED)
    ax.text(110, 2.2, "Every step appends an audit event (actor, action, salted commitment: no names, no answer text). Priority = stakes x discrepancy (Routine / Priority / Urgent).",
            ha="center", fontsize=8.3, color=MUTED)
    save(fig, FIG / "fig04_governance_workflow.png")


# ============================================================ revised blueprint
def fig_revised():
    fig, ax = canvas(200, 108)
    ax.text(100, 104, "Task 6: revised blueprint after changed evidence (inconsistent labels, partner withdrawn, halved budget)",
            ha="center", fontsize=14.5, fontweight="bold")
    zone(ax, 2, 40, 120, 58, "Production examination path (unchanged core)", ec=BLUE)
    box(ax, 6, 76, 28, 14, "Clients\n(student, examiner,\nmoderator, controller)", fc=TEAL_L, ec=TEAL, fs=8.5, bold=True)
    box(ax, 40, 76, 24, 14, "API gateway\nRBAC, validation", fc=BLUE_L, ec=BLUE, fs=8.5, bold=True)
    box(ax, 70, 76, 48, 14, "Rubric-rule assistant (v2) + workflow\nblind-first; abstains; no approval rights", fc=BLUE_L, ec=BLUE, fs=8.5, bold=True)
    route(ax, [(34, 83), (40, 83)], lw=1.4); route(ax, [(64, 83), (70, 83)], lw=1.4)
    box(ax, 6, 46, 36, 16, "Marks DB (S): versioned corrections\nreduced retention of samples", fc=RED_L, ec=RED, fs=8.2, bold=True)
    box(ax, 48, 46, 34, 16, "Restricted content store (S)\ncontent erasable on request", fc=RED_L, ec=RED, fs=8.2, bold=True)
    box(ax, 88, 46, 30, 16, "Audit chain: salted\ncommitments only", fc=SLATE_L, ec=SLATE, fs=8.2, bold=True)
    for x in (24, 65, 103):
        route(ax, [(x, 76), (x, 62)], lw=1.3, both=True, head=8)
    tag(ax, 6, 62, "R2", fc=GREEN)
    box(ax, 126, 74, 70, 20, "Internal audit office\ndaily head-hash + entry count published\n(closes truncation and privileged-edit gaps T3, T5)", fc=GREEN_L, ec=GREEN, fs=8.2, bold=True)
    route(ax, [(118, 54), (122, 54), (122, 84), (126, 84)], color=GREEN, lw=1.5, ls="--")
    tag(ax, 126, 94, "R3", fc=GREEN)
    box(ax, 126, 44, 70, 22, "Credential service: signed certificate\n+ public verification page (conventional)\nno partner dependency; retry-safe issue", fc=VIOLET_L, ec=VIOLET, fs=8.2, bold=True)
    tag(ax, 126, 66, "R4", fc=VIOLET)
    box(ax, 2, 6, 92, 26, "Future ML evaluation environment: SEPARATE and OFFLINE\ntraining for Operating Systems SUSPENDED\nGate: two experts re-label a sample, kappa >= 0.6, then a bounded pilot\nbudget check: ML path ~442 CPU-s per cycle > halved budget 300 (estimate)",
        fc="#fff", ec=SLATE, fs=8.4, ls="--", color=MUTED)
    tag(ax, 2, 32, "R5", fc=SLATE)
    box(ax, 104, 6, 92, 26, "Blockchain ledger: REMOVED\npartner institution withdrew; no independent participants;\nerasure of sensitive corrections conflicts with immutable copies (T7a)\ncertificate verification stays conventional",
        fc="#fff", ec=RED, fs=8.4, ls="--", color=RED)
    ax.plot([105, 195], [7, 31], color=RED, lw=1.1, zorder=6); ax.plot([105, 195], [31, 7], color=RED, lw=1.1, zorder=6)
    tag(ax, 104, 32, "R6", fc=RED)
    route(ax, [(60, 40), (60, 32)], color=SLATE, lw=1.2, ls="--", head=8)
    label(ax, 74, 36, "no connection to the live path", fs=7.4, color=SLATE, bold=True)
    ax.text(100, 1.5, "R1 abstain on unexplained terms (v2)   R2 commitments not content   R3 external head-hash   R4 no partner dependency   R5 ML deferred   R6 ledger excluded",
            ha="center", fontsize=8.4, color=MUTED)
    save(fig, FIG / "fig05_revised_blueprint.png")


if __name__ == "__main__":
    for f in (fig_stakeholders, fig_components, fig_dfd, fig_workflow, fig_revised):
        f()
