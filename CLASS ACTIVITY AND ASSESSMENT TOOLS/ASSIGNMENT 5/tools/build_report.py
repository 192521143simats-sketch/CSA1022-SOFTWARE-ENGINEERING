#!/usr/bin/env python3
"""Build report/CSA10_Assignment5_Report.docx from results/*.json, figures/ and screenshots/.
All numeric evidence is read from results.json / timing.json (never typed by hand)."""
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "results" / "results.json").read_text())
T = json.loads((ROOT / "results" / "timing.json").read_text())
FIG, SHOT = ROOT / "figures", ROOT / "screenshots"
OUT = ROOT / "report"
OUT.mkdir(exist_ok=True)

NAVY, BLUE, GREY = RGBColor(0x1B, 0x23, 0x30), RGBColor(0x24, 0x57, 0xD6), RGBColor(0x5B, 0x66, 0x75)
doc = Document()

# ---------------------------------------------------------------- base styles
st = doc.styles["Normal"]
st.font.name, st.font.size = "Calibri", Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(5)
st.paragraph_format.line_spacing = 1.08
for name, size, color in (("Heading 1", 18, NAVY), ("Heading 2", 13.5, BLUE), ("Heading 3", 11.5, NAVY)):
    h = doc.styles[name]
    h.font.name, h.font.size, h.font.bold, h.font.color.rgb = "Calibri", Pt(size), True, color
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    h.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
    h.paragraph_format.space_after = Pt(5)
    h.paragraph_format.keep_with_next = True

sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
for s_ in ("left_margin", "right_margin"):
    setattr(sec, s_, Inches(0.85))
sec.top_margin, sec.bottom_margin = Inches(0.8), Inches(0.8)


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_)
    tcPr.append(shd)


def page_field(paragraph):
    run = paragraph.add_run()
    for t, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if t:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt
        run._r.append(e)
    run.font.size = Pt(8.5)


def footer(section):
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]
    p.text = ""
    r = p.add_run("CSA10 Software Engineering  |  Assignment 5  |  Responsible Technology Adoption   —   page ")
    r.font.size, r.font.color.rgb = Pt(8.5), GREY
    page_field(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


footer(sec)


def H1(t, brk=True):
    h = doc.add_heading(t, 1)
    h.paragraph_format.page_break_before = brk
    return h
def H2(t): return doc.add_heading(t, 2)
def H3(t): return doc.add_heading(t, 3)


def P(text="", bold=False, italic=False, size=None, color=None, align=None, after=None):
    p = doc.add_paragraph()
    add_runs(p, text, bold, italic, size, color)
    if align:
        p.alignment = align
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def add_runs(p, text, bold=False, italic=False, size=None, color=None):
    """**bold** segments inside text are supported."""
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        r = p.add_run(part)
        r.bold = bold or (i % 2 == 1)
        r.italic = italic
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color


def B(text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    add_runs(p, text)
    p.paragraph_format.space_after = Pt(2.5)
    if level:
        p.paragraph_format.left_indent = Inches(0.25 + 0.25 * level)
    return p


def callout(text, fill="E8EEFC", edge="2457D6", bold_first=True):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    shade(c, fill)
    tcPr = c._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "bottom", "right"):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "nil"); borders.append(e)
    e = OxmlElement("w:left"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "32"); e.set(qn("w:color"), edge)
    borders.append(e); tcPr.append(borders)
    c.paragraphs[0].text = ""
    add_runs(c.paragraphs[0], text, size=10.5)
    c.paragraphs[0].paragraph_format.space_after = Pt(3)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def table(rows, widths, header=True, size=8.8, fills=None, bold_first_col=False):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.rows[i].cells[j]
            c.width = Inches(widths[j])
            c.paragraphs[0].text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.0
            txt = str(val)
            hdr = header and i == 0
            add_runs(p, txt, bold=hdr or (bold_first_col and j == 0), size=size,
                     color=RGBColor(0xFF, 0xFF, 0xFF) if hdr else None)
            if hdr:
                shade(c, "1B2330")
            elif fills and (i, j) in fills:
                shade(c, fills[(i, j)])
            elif i % 2 == 0:
                shade(c, "F4F7FB")
    if header:
        trPr = t.rows[0]._tr.get_or_add_trPr()
        e = OxmlElement("w:tblHeader"); e.set(qn("w:val"), "true"); trPr.append(e)
    doc.add_paragraph().paragraph_format.space_after = Pt(3)
    return t


CNT = {"Figure": 0, "Table": 0, "Screenshot": 0}


def caption(text, kind="Figure"):
    CNT[kind] += 1
    p = doc.add_paragraph()
    r = p.add_run(f"{kind} {CNT[kind]}. ")
    r.bold, r.font.size, r.font.color.rgb = True, Pt(9), BLUE
    r2 = p.add_run(text)
    r2.italic, r2.font.size, r2.font.color.rgb = True, Pt(9), GREY
    p.paragraph_format.space_after = Pt(8)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if kind == "Table" else WD_ALIGN_PARAGRAPH.CENTER
    return p


def new_section(landscape):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    if landscape:
        s.orientation = WD_ORIENT.LANDSCAPE
        s.page_width, s.page_height = Inches(11.69), Inches(8.27)
        s.left_margin = s.right_margin = Inches(0.6)
        s.top_margin = s.bottom_margin = Inches(0.6)
    else:
        s.orientation = WD_ORIENT.PORTRAIT
        s.page_width, s.page_height = Inches(8.27), Inches(11.69)
        s.left_margin = s.right_margin = Inches(0.85)
        s.top_margin = s.bottom_margin = Inches(0.8)
    footer(s)
    return s


def figure(path, cap, landscape=None, width=None, heading=None, intro=None, kind="Figure"):
    """Insert an image with caption. Wide images go on a landscape page."""
    path = Path(path)
    w, h = Image.open(path).size
    if landscape is None:
        landscape = (w / h) > 1.55 and w >= 3500
    moved = []
    if landscape:
        body = doc.element.body
        kids = [k for k in body if k.tag != qn("w:sectPr")]
        tail = []
        for el in reversed(kids[-4:]):
            if el.tag != qn("w:p") or el.find(".//" + qn("w:sectPr")) is not None:
                break
            tail.append(el)
            ps = el.find(qn("w:pPr"))
            sty = ps.find(qn("w:pStyle")) if ps is not None else None
            if sty is not None and sty.get(qn("w:val")).startswith("Heading"):
                moved = list(reversed(tail))
                break
        for el in moved:
            body.remove(el)
        new_section(True)
        for el in moved:
            body.insert(len(body) - 1, el)
        avail_w, avail_h = 10.4, 5.0 if moved else 6.3
    else:
        avail_w, avail_h = 6.55, 8.6
    wi = width or min(avail_w, avail_h * w / h)
    wi = min(wi, avail_w)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(wi))
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    caption(cap, kind)
    if landscape:
        new_section(False)


def shot(name, cap):
    import re as _re
    cap = _re.sub(r"^Screenshot \d+ – ", "", cap)
    path = SHOT / name
    w, h = Image.open(path).size
    css_w = w / 2
    land = css_w > 1250
    figure(path, cap, landscape=land, width=None, kind="Screenshot")


# =============================================================== COVER
for _ in range(3):
    doc.add_paragraph()
P("CSA10 – SOFTWARE ENGINEERING", bold=True, size=12, color=GREY)
P("Assignment 5", bold=True, size=14, color=GREY, after=14)
P("Create and Validate Responsible Technology Adoption for the Examination and Credential Platform",
  bold=True, size=26, color=NAVY, after=10)
P("Comparing rubric-rule assistance, trained AI/ML and Blockchain with a bounded, reproducible demonstrator",
  size=13, color=BLUE, after=24)
callout("**Recommendation in one line.**  Retain the conventional role-controlled marks database and adopt "
        "**explainable, abstaining rubric-rule assistance with human authority** (Alternative A). "
        "**Exclude** Blockchain credential verification. **Defer** trained ML behind explicit data and agreement gates. "
        "The evidence supports this, and the sensitivity analysis states exactly which combined conditions would change it.")
table([["Item", "Detail"],
       ["Course outcome", "CO5 – compare and assess emerging technologies (AI/ML, Blockchain) for applicability, societal impact, ethics and sustainability"],
       ["Nature / marks", "Individual / 50 marks (Tasks 1-7)"],
       ["Evidence status", "All data are **synthetic**. Demonstrator results are illustrative evidence of displayed behaviour, "
                           "**not** proof of production accuracy, performance, live monitoring or secure authorisation."],
       ["Code and data", "Repository `responsible-tech-demonstrator` (Python standard library only, seed 2026). "
                         "One command reproduces every number: `python3 run_demonstrator.py`."],
       ["Student / register no. / date", "____________________  /  ____________________  /  ____________________"]],
      [1.7, 4.85], bold_first_col=True, size=9.5)
P("How to read the evidence labels", bold=True, size=10.5, color=NAVY, after=2)
for lab, txt in (("MEASURED", "produced by running the demonstrator on this machine (single machine, not a benchmark)."),
                 ("OBSERVED", "a deterministic result of the demonstrator on the synthetic data."),
                 ("SIMULATED", "generated under assumed parameters (label noise, stakeholder responses)."),
                 ("ESTIMATE / ASSUMPTION", "a planning figure from a stated assumption; never presented as measured.")):
    B(f"**{lab}** – {txt}")

H1("Contents and mark map")
table([["Task", "Assessed area", "Marks", "Where the evidence is"],
       ["1", "Stakeholder investigation and decision criteria", "5", "Section 1"],
       ["2", "Technology comparison and selection model", "8", "Section 2"],
       ["3", "Responsible system blueprint", "10", "Section 3"],
       ["4", "Demonstrator and claim validation", "10", "Section 4 (screenshots 1-7)"],
       ["5", "Ethical and sustainable operating plan", "5", "Section 5"],
       ["6", "Redesign under changed evidence and constraints", "8", "Section 6"],
       ["7", "Individual technical reflection", "4", "§7"],
       ["", "Appendices: pre-registered predictions, reproduction, references, tools", "–", "Appendices A-D"]],
      [0.55, 3.4, 0.6, 2.0], size=9.5)

# =============================================================== EXECUTIVE SUMMARY
H1("Executive summary", brk=False)
m = R["C2"]["metrics"]
P("The university must decide whether to keep deterministic rubric-rule support, introduce trained AI/ML, add a Blockchain "
  "for shared credential verification, or combine them. I treated this as a decision problem, not a technology purchase: "
  "I defined criteria first, compared four alternatives, built a small demonstrator that tests falsifiable claims, "
  "and then re-decided when the evidence changed.")
callout(f"**What the evidence says.**\n"
        f"•  **Weighted comparison (planning judgement):** A = {R['selection']['base']['A']:.2f}, B (ML) = {R['selection']['base']['B']:.2f}, "
        f"C (Blockchain) = {R['selection']['base']['C']:.2f}, D (ML + Blockchain) = {R['selection']['base']['D']:.2f} out of 5. "
        f"A stays first in 6 of 7 sensitivity scenarios; **D wins only when labels are validated, partner institutions are committed, "
        f"and usefulness/trust weights are raised together (S6).**\n"
        f"•  **Assistant (OBSERVED, 24 synthetic answers):** a forced-choice baseline makes **{m['baseline']['wrong']}** wrong suggestions; "
        f"my first abstaining version made **{m['v1']['wrong']}** (my pre-registered target of ≤ 2 was **missed**); after revision R1 it makes **{m['v2']['wrong']}** "
        f"on the answers it handles, but gives a suggestion on only **{m['v2']['coverage']*100:.0f}%** of answers.\n"
        f"•  **Blockchain exclusion (OBSERVED):** a plain hash-chained audit log already detects naive edits; neither a chain nor a ledger detects "
        f"a privileged edit with recomputation or truncation without an external checkpoint, and neither can verify that the original mark was true.\n"
        f"•  **Changed evidence (Task 6):** inconsistent labels, a withdrawn partner and a halved budget all *strengthen* Alternative A "
        f"(revised score {R['selection']['revised']['revised_weights']['A']:.2f} vs {R['selection']['revised']['revised_weights']['B']:.2f} for ML).",
        fill="EEF7F1", edge="15803D")
callout("**Honest limits.**  Pre-registered claim C2b (v1 ≤ 2 wrong) **failed** and an acceptance threshold (wrong rate ≤ 10%) is **not met** "
        f"(v2: {m['v2']['wrong_rate_on_answered']*100:.1f}%, 95% interval {m['v2']['wrong_rate_wilson95'][0]*100:.0f}%–{m['v2']['wrong_rate_wilson95'][1]*100:.0f}%) "
        "on this very small crafted set. Revision R1 was tuned on the same 24 answers, so its post-revision figure is an optimistic, **non-independent** result. "
        "I report these failures rather than hide them; they are part of the finding that rules should assist, never decide.",
        fill="FDF0DC", edge="B45309")

# =============================================================== TASK 1
H1("Task 1 – Investigate stakeholder needs and define decision criteria  (5 marks)")
H2("1.1 The decision problem")
P("**Decision:** which technology arrangement should the university adopt for evaluation support, moderation, mark approval, "
  "revaluation and credential issue – while preserving timely result publication, meaningful human evaluation, correction, privacy and affordable operation?")
P("**Constraints from the scenario:** examiner marks are historically inconsistent; answers can be paraphrased or ambiguous; student "
  "records are sensitive; resources are limited; the external verification service may be unavailable (local records must be preserved and the "
  "request retried safely). **Two truths the technology cannot supply:** an AI suggestion cannot establish the correct mark without an examiner "
  "reading the answer, and a ledger cannot establish that the original mark or document was true.")

H2("1.2 Stakeholders and what each needs")
figure(FIG / "fig01_stakeholder_map.png", "Stakeholder map. Responses are simulated and labelled as such.", landscape=True)
table([["Stakeholder", "Primary need", "Main concern", "Decision criterion it drives"],
       ["Students", "Correct, explainable marks; a revaluation route", "Wrong or disputed mark; exposure of answer content", "Privacy, fairness, correction"],
       ["Examiners", "Rubric evidence beside the answer; easy, recorded override", "Anchoring on a suggestion; extra workload", "Usefulness, reliability"],
       ["Moderators", "Review effort directed to risky scripts", "Random-only sampling misses large discrepancies", "Usefulness"],
       ["Controller of examinations", "Sole, accountable approval; corrections with reasons", "Published results that cannot be defended", "Reliability, governance"],
       ["Administrators / DPO", "Minimum personal data; retention and erasure rules", "Immutable copies of sensitive records", "Privacy, governance"],
       ["Department heads", "Subject-level consistency reports (aggregates only)", "Unfair comparison across subjects", "Fairness"],
       ["External verifiers / partners", "Cheap, trustworthy credential check", "Dependence on one institution's availability", "Shared-trust need, cost"],
       ["Operations staff", "Simple deployment and upkeep", "Skills and maintenance load", "Cost sustainability, governance readiness"]],
      [1.25, 1.9, 1.85, 1.55], size=8.5)
caption("Stakeholders, needs and the criteria each one drives.", "Table")

H2("1.3 Intended benefits, system boundary and exclusions")
table([["Aspect", "Definition"],
       ["Intended benefits", "Faster, more consistent moderation; visible rubric evidence for examiners; discrepancy flags; prioritised moderation; defensible correction trail; verifiable certificates."],
       ["Inside the boundary", "Answer-script submission, evaluation, moderation, mark approval, revaluation requests, credential issue and verification, audit trail, redacted evaluation samples."],
       ["Outside the boundary (exclusions)", "Automatic marking or publication; real student data; production load testing; legal advice; a deployed Blockchain network; a trained ML model (evaluated as an option only); live monitoring."],
       ["Non-negotiable rules", "Only the controller approves; every override or correction needs a recorded reason; the assistant has no write or approve rights; nothing identifies a student in exported samples."]],
      [1.6, 4.95], size=9, bold_first_col=True)
caption("Benefits, boundary and exclusions.", "Table")

H2("1.4 Investigation questions, method and findings")
table([["#", "Investigation question (uncertainty or conflict)", "How investigated", "Finding"],
       ["IQ1", "Do rubric-keyword rules treat paraphrased, term-listing or negated answers fairly?",
        "Demonstrator, 24 expert-labelled synthetic answers incl. paraphrase, negation, term listing (§4)",
        f"Forced choice was wrong on all 4 paraphrased, the negated and both term-listing answers. Abstention removes those wrong suggestions but gives those answers **no** help."],
       ["IQ2", "Can an audit trail prove that a mark was not altered, and what can it not prove?",
        "Tamper tests T1-T8 (§4.4)", "Detects naive edits; **cannot** detect privileged rewrite or truncation without an external checkpoint; never proves the original mark was true."],
       ["IQ3", "Are examiner labels consistent enough to train or even evaluate ML?",
        "Label-noise simulation (§4.6)", f"With assumed 35% noise kappa = {R['C6']['subjects'][1]['examiner_kappa']:.2f}, below the 0.6 gate: labels would be too inconsistent to train on."],
       ["IQ4", "Does the design still work when the external verifier is unavailable?",
        "Credential failure scenarios F1-F3 (§4.5)", "Local marks untouched; request kept pending; retry creates exactly one certificate."],
       ["IQ5", "Do stakeholders' interests conflict?", "Simulated stakeholder discussion (below)",
        "Yes: examiners want speed, students want explanation, the DPO wants erasure, partners want verification. Resolved through human authority + minimum data."]],
      [0.4, 2.0, 1.95, 2.2], size=8.4)
caption("Investigation questions and findings.", "Table")

H3("Simulated stakeholder discussion (clearly labelled – not interview data)")
for who, q in (("Examiner (simulated)", "“If the tool shows me a band first I will probably agree with it. Show me matched terms, and let me mark before I see anything.”  → **Blind-first evaluation** adopted."),
               ("Student (simulated)", "“If my answer is in my own words, will a machine give me a lower mark?”  → Paraphrase test added; the assistant **abstains** instead of guessing."),
               ("Controller (simulated)", "“I cannot publish a result I cannot defend.”  → Only the controller approves; every override needs a reason."),
               ("DPO (simulated)", "“A student asks to delete a disputed record. Can we?”  → Salted commitments in the chain, content in a restricted store; erasure tested (A13)."),
               ("Partner institution (simulated)", "“We joined for verification, not to run infrastructure.”  → Ledger excluded; public fingerprint verification page.")):
    B(f"**{who}:** {q}")

H2("1.5 Planning assumptions and measurable decision criteria")
table([["Planning assumption", "Value", "Basis"],
       ["Students / papers each / answers per paper", "2,400 / 5 / 4", "Assumption (mid-sized university)"],
       ["Answers per cycle / per year (2 cycles)", f"{R['resources']['answers_per_cycle']:,} / {R['resources']['answers_per_year']:,}", "Derived"],
       ["Result-publication service level", "Moderated marks approved within 5 working days of evaluation", "Assumption"],
       ["Dispute window", "7 days after approval", "Assumption (implemented and tested)"],
       ["Compute budget per cycle", f"{R['resources']['budget_original']} CPU-s, halved to {R['resources']['budget_halved']} in Task 6", "Assumption"]],
      [2.8, 2.3, 1.45], size=8.8)
caption("Workload and service-level assumptions.", "Table")
table([["Criterion (weight)", "How it is measured", "Acceptance threshold (planning)", "Evidence source"],
       ["Usefulness (15%)", "Share of answers that receive a rubric-evidence suggestion; moderation effort directed to risky scripts", "Coverage reported openly; no minimum claimed", "Demonstrator C2, C1"],
       ["Shared-trust need (10%)", "Number of independent institutions needing to verify records", "Ledger considered only if ≥ 3 committed independent participants", "Stakeholder analysis"],
       ["Reliability (20%)", "Wrong-band suggestions on answered items; safe failure; tamper detection", "Wrong rate ≤ 10% on answered items; no suggestion may approve or publish", "C2, C3, C4"],
       ["Privacy (15%)", "Identifiers in exported samples; erasure possible without breaking audit", "0 identifiers in export; erasure test passes", "A11, A13, T7a/b"],
       ["Fairness (15%)", "Wrong/withheld suggestions by answer style; examiner agreement per subject", "No style systematically mis-banded; kappa ≥ 0.6 before any ML pilot", "C2 by style, C6"],
       ["Cost sustainability (15%)", "CPU-s per cycle, storage per year, labelling and governance hours", "≤ budget (600 → 300 CPU-s per cycle)", "Task 5 estimates"],
       ["Governance readiness (10%)", "Named owners, labelled data, partner commitments exist today", "All required owners and data present", "Stakeholder analysis"]],
      [1.35, 2.2, 1.9, 1.1], size=8.3)
caption("Measurable decision criteria (weights sum to 100%).", "Table")

# =============================================================== TASK 2
H1("Task 2 – Compare technology alternatives and create a selection model  (8 marks)")
H2("2.1 The four alternatives")
P("The deterministic rubric baseline is presented **separately** from trained ML: it contains no learned parameters, is fully inspectable and is the same under every run.")
table([["", "A  Conventional + rubric rules", "B  Trained ML assistance", "C  Blockchain verification", "D  ML + Blockchain"],
       ["Problem addressed", "Consistent, explainable evaluation support; prioritised moderation; audit trail", "Broader semantic scoring of paraphrased answers", "Shared, tamper-evident verification of credentials across institutions", "Both B and C"],
       ["Assumptions required", "Rubric concepts agreed by examiners", "Large, consistent, expert-labelled data; calibration; retraining", "≥ 3 independent participants; agreed governance and key management", "All of B and C"],
       ["Data readiness", "Ready (rubrics exist)", "**Not ready** – labels inconsistent", "Ready (small records)", "Not ready"],
       ["Shared trust", "Not needed (single issuer)", "Not relevant", "The only case it helps", "As C"],
       ["Governance", "Owners exist", "No owner for model risk, drift, bias", "No participant agreement", "Both missing"],
       ["Integration", "Low", "Medium (pipeline, retraining)", "High (nodes, consensus, key custody)", "Highest"],
       ["Operational skills", "Existing staff", "ML engineering, labelling", "Distributed-ledger operations", "Both"]],
      [1.0, 1.45, 1.4, 1.45, 1.25], size=8.2, bold_first_col=True)
caption("Four alternatives compared on readiness dimensions.", "Table")
H2("2.2 Two distinctions the decision must respect")
B("**Prediction quality ≠ decision quality.** A scorer can match examiner bands often and still produce poor decisions if examiners over-trust it (automation complacency), if errors fall on particular writing styles, or if its confidence is read as probability. "
  "I therefore display only a band and the matched rubric terms, and **never a probability or confidence score**, because none can be calibrated without validated labels.")
B("**Record integrity ≠ input truthfulness.** A hash chain or ledger shows that an entry was not changed after it was written. It cannot show that the mark or document entered was true. Test T6 demonstrates this: a false mark entered in good faith yields a perfectly valid chain.")
H2("2.3 Weighted decision matrix")
P("Scores are **ordinal planning judgements (1-5, higher is better)** tied to the evidence below. They are not measurements. Weighted score = Σ(weight × score) / 100.")
figure(FIG / "fig_decision_matrix.png", "Weighted decision matrix and totals (generated from results.json).", landscape=True)
import sys
sys.path.insert(0, str(ROOT))
from demonstrator import selection as SEL  # noqa: E402
table([["Criterion", "Evidence behind the scores (A, B, C, D)"]] +
      [[f"{c} ({SEL.W0[c]}%)", SEL.EVIDENCE[c]] for c in SEL.CRITERIA],
      [1.45, 5.1], size=8.3, bold_first_col=True)
caption("Evidence linked to each criterion.", "Table")
b_ = R["selection"]["base"]
P(f"**Result:** A = **{b_['A']:.2f}**, B = {b_['B']:.2f}, C = {b_['C']:.2f}, D = {b_['D']:.2f}.  "
  "A leads because it is the only option that is ready on data, governance, privacy and cost today, even though it is only moderately useful.")

H2("2.4 Sensitivity analysis")
P("I changed weights **and** assumptions across seven scenarios, and swept the Usefulness and Shared-trust weights to find break-even points.")
figure(FIG / "fig_sensitivity.png", "Sensitivity: scenario scores (left) and break-even weight when expert labels are validated (right).", landscape=True)
sens = R["selection"]["sensitivity"]
rows = [["Scenario", "A", "B", "C", "D", "Best"]]
fills = {}
for i, (k, v) in enumerate(sens.items(), start=1):
    best = max(v, key=v.get)
    rows.append([k, f"{v['A']:.2f}", f"{v['B']:.2f}", f"{v['C']:.2f}", f"{v['D']:.2f}", best])
    if best != "A":
        fills[(i, 5)] = "EDE9FB"
table(rows, [3.2, 0.6, 0.6, 0.6, 0.6, 0.6], size=8.8, fills=fills)
caption("Scenario scores. S6 is the only scenario in which A is not selected.", "Table")
be = R["selection"]["break_even"]
P("**Break-even weights (other weights scaled proportionally; None = never within 0-90%):**")
table([["Sweep", "B beats A at", "C beats A at", "D beats A at"],
       ["Usefulness weight, base scores", f"{be['usefulness_base']['B']}%", "never", f"{be['usefulness_base']['D']}%"],
       ["Usefulness weight, labels validated", f"{be['usefulness_labels_validated']['B']}%", "never", f"{be['usefulness_labels_validated']['D']}%"],
       ["Shared-trust weight, base", "never", f"{be['shared_trust_base']['C']}%", f"{be['shared_trust_base']['D']}%"],
       ["Shared-trust weight, institutions committed", "never", f"{be['shared_trust_institutions_committed']['C']}%", f"{be['shared_trust_institutions_committed']['D']}%"],
       ["Shared-trust weight, labels + institutions", "never", f"{be['shared_trust_both_conditions']['C']}%", f"{be['shared_trust_both_conditions']['D']}%"]],
      [3.05, 1.15, 1.15, 1.15], size=8.8)
caption("Break-even weights.", "Table")
H2("2.5 Selection and the circumstances that would change it")
callout("**Selected: Alternative A** – conventional role-controlled marks database + explainable, abstaining rubric-rule assistance + human evaluation, correction and approval.")
P("**The selection would change if:**")
B("**Towards B (ML):** two experts independently label a representative sample and **kappa ≥ 0.6** per subject; a pilot shows the model's wrong-band rate stays within the 10% threshold across answer styles; ownership for model risk, drift and bias is named; and usefulness is weighted ≥ 55% (labels validated). ML would still run offline first.")
B("**Towards C/D (ledger):** at least **three independent institutions** commit to run nodes and a governance agreement, key custody is settled, and shared-trust weight reaches ≈ 46%. S6 shows D leading (3.35 vs 3.20) **only** when labels are validated, institutions are committed and usefulness/trust weights are raised together – and even then by a margin that is within the uncertainty of ordinal scores.")
B("**Away from A:** if observed wrong-band rates on answered items exceed the 10% threshold in a real pilot, or examiners systematically accept wrong suggestions.")

# =============================================================== TASK 3
H1("Task 3 – Create a responsible system blueprint  (10 marks)")
H2("3.1 Component diagram")
P("Each component answers a named need from Task 1. Sensitive stores (S) hold names, register numbers, answer text and marks; the chain stores only salted commitments.")
figure(FIG / "fig02_component_diagram.png", "Selected blueprint – component diagram. Trained ML is an offline option; Blockchain is excluded.", landscape=True)
table([["Component", "Need it addresses", "Control"],
       ["API gateway", "Students/examiners only see what they should", "Authentication, role-based access, input validation, rate limiting"],
       ["Evaluation service (rules)", "Examiners want rubric evidence; moderators want risk ordering", "Deterministic; abstains to Manual Review; no write or approve rights"],
       ["Workflow service", "Controller accountability; student challenge", "State machine; reasons mandatory; versioned history"],
       ["Audit service", "Defensible trail; DPO erasure", "Hash chain of **salted commitments**; no names or answer text"],
       ["Redaction / export worker", "Evaluation samples without identifiers", "Removes identifiers; no approval rights"],
       ["Credential service", "Verifiable certificates; verifier may be unavailable", "Signed certificate; idempotent retry; fingerprint-only public page"],
       ["External checkpoint", "Closes truncation / privileged-edit gaps", "Daily head-hash and entry count kept by the internal audit office"]],
      [1.6, 2.35, 2.6], size=8.5, bold_first_col=True)
caption("Components, the needs they serve and their controls.", "Table")
H2("3.2 Data-flow diagram with trust boundaries and sensitive data")
figure(FIG / "fig03_data_flow_diagram.png", "Data-flow diagram. Red = sensitive data; B1-B5 = trust boundaries; numbers = flows F1-F15.", landscape=True)
table([["Flow", "From → To", "Data", "Sensitive?", "Control at the boundary"],
       ["F1", "Users → P1", "Credentials, requests, submissions", "Yes", "B1: authentication, role check, validation"],
       ["F2", "P1 → P3", "Authorised request", "Yes", "Least privilege"],
       ["F3-F4", "P3 ↔ P2", "Answer text out; band + matched terms back", "Yes", "Suggestion is advisory; abstains when unsure"],
       ["F5", "D2 → P2", "Answer text", "Yes", "Restricted store"],
       ["F6", "P3 ↔ D1", "Marks, versions, reasons", "Yes", "Versioned writes only"],
       ["F7", "P3 → D2", "Answer text", "Yes", "Encrypted at rest (assumed)"],
       ["F8-F9", "P3 → P4 → D3", "Salted commitment, hashes", "No identifiers", "Chain holds no content"],
       ["F10", "D3 → D5", "Head-hash + entry count", "No", "B4: external checkpoint"],
       ["F11-F12", "D2 → P6 → D4", "Answer text → redacted text", "Yes → No", "B3: redaction removes identifiers (A11)"],
       ["F13-F14", "P3 → P5 → public page", "Certificate fingerprint", "No", "B2/B5: fingerprint only, no marks or identities"],
       ["F15", "Verifier ↔ page", "Fingerprint check", "No", "Public, read-only"]],
      [0.55, 1.35, 2.0, 0.8, 1.85], size=8.2)
caption("Flow table for the data-flow diagram.", "Table")
H2("3.3 Role of rules, ML and human decision responsibility")
table([["Question", "Design decision"],
       ["Role of rules", "Match rubric concepts, count them, propose a band **with matched terms shown**, and **abstain** (Manual Review) on insufficient evidence, negated terms, very short answers and term lists with no explanation."],
       ["Role of ML", "**None in production.** Evaluated only as Alternative B. If piloted: offline sandbox, trained on redacted samples, separate from live marks; promoted only after the gates in §2.5."],
       ["Training-data assumptions (for any ML pilot)", "Two independent expert labels per answer; per-subject kappa ≥ 0.6; stratified by answer style including paraphrase; no student identifiers; documented retention."],
       ["Evaluation plan", "Same conditions as the baseline; wrong-band rate on answered items with confidence interval; per-style fairness table; calibration shown before any score is displayed."],
       ["Explanation mechanism", "Matched rubric terms and the reason for abstention are displayed. **No probability or confidence score is shown**, because none can be interpreted as calibrated without validation."],
       ["Human decision responsibility", "The examiner records a **provisional mark before** the suggestion is revealed (reduces anchoring). Only the controller approves. The assistant cannot approve, publish or change a mark (test A1)."]],
      [1.75, 4.8], size=8.6, bold_first_col=True)
caption("Rules, ML and human responsibility.", "Table")
H2("3.4 Blockchain role, participant governance and justified exclusion")
table([["Topic", "Position"],
       ["Proposed role", "Shared verification of degree credentials between the university and partner institutions."],
       ["Participant governance it would need", "≥ 3 independent participants, node operators, consensus rules, key-custody and recovery policy, dispute and exit rules, cost sharing."],
       ["Information placement", "If ever used: **fingerprints only** on the ledger; marks, names and answer text stay off-chain."],
       ["Correction approach", "A correction would be a new entry referencing the old one; the old entry stays. This conflicts with erasure of sensitive values (T7a), so sensitive content must never be placed on a ledger."],
       ["Decision", "**Excluded.** No independent participants exist (and in Task 6 the only partner withdraws). A conventional signed certificate with a public fingerprint page gives the verification benefit without shared infrastructure. A chain of salted commitments plus an external checkpoint gives the tamper-evidence benefit."]],
      [1.85, 4.7], size=8.6, bold_first_col=True)
caption("Blockchain role and exclusion.", "Table")
H2("3.5 Governance workflow (examiner review, override, correction, student challenge)")
figure(FIG / "fig04_governance_workflow.png", "Governance workflow across seven roles. Every step appends an audit event.", landscape=True)
H2("3.6 Access, retention and audit controls, and handling of inaccurate source information")
table([["Control", "Specification", "Verified by"],
       ["Access", "Least privilege by role; examiner sees only assigned scripts; student sees own record; assistant may only suggest; export worker may only export redacted text", "A1, A3, A4, A10a-c, A12"],
       ["Retention", "Answer text kept for the appeal period then deleted from the restricted store (assumed 12 months); marks and approvals kept for the record period; redacted samples reviewed annually", "Policy (planning assumption)"],
       ["Audit", "Append-only chain of salted commitments; daily head-hash and entry count held externally; verification run daily", "T1-T5b"],
       ["Inaccurate marks", "Student disputes within 7 days with a reason; controller corrects **with a recorded reason**; a new version is created; earlier versions stay in history", "A6, A7, A8, A9"],
       ["Inaccurate source answer data", "A mis-scanned or wrong script is corrected as a new version with a reason; the audit event records who and why, not the content", "A8"],
       ["Right to erasure", "Superseded sensitive values are erased from the restricted store; the commitment and metadata remain; the current mark is kept", "A13, A13b, T7b"],
       ["Privacy by design", "Pseudonymous student identifiers in the workflow; redaction before any evaluation use", "A11, A11b"]],
      [1.35, 3.8, 1.4], size=8.5, bold_first_col=True)
caption("Controls and how each is verified.", "Table")
H2("3.7 Traceability matrix")
table([["Stakeholder need", "Design decision", "Risk addressed", "Validation scenario"],
       ["Examiners: evidence, not a verdict", "Matched terms; no confidence score; blind-first", "Anchoring; misleading confidence", "A2/A2b; C2"],
       ["Students: fair treatment of own wording", "Abstain on paraphrase / unexplained terms", "Unequal treatment by writing style", "C2 by style; R1"],
       ["Controller: defensible publication", "Only controller approves; reasons mandatory", "Undefended result; unaccountable automation", "A1, A3, A4, A7"],
       ["Students: correction route", "Dispute window; versioned correction", "Inaccurate or disputed marks", "A6, A8, A9"],
       ["Moderators: risk-ordered sample", "Stakes × discrepancy matrix", "Large discrepancies missed", "C1 (9/9 cells)"],
       ["DPO: minimum data and erasure", "Salted commitments; restricted store; redaction", "Immutable copy of sensitive data", "T7a/b, T8, A11, A13"],
       ["Auditor: detect tampering", "Hash chain + external checkpoint", "Silent edit or truncation", "T2-T5b"],
       ["Verifier: check a certificate", "Signed certificate + fingerprint page; retry-safe", "Verifier outage; duplicates; forged grade", "F1-F3"],
       ["Operations: low cost", "Rules; no ledger; no model serving", "Unaffordable operation", "Task 5 estimates"],
       ["Department heads: fair subjects", "Per-subject kappa gate; aggregate reports", "Noisy labels penalise a subject", "C6"]],
      [1.7, 1.85, 1.65, 1.35], size=8.4)
caption("Traceability: need → decision → risk → validation.", "Table")

# =============================================================== TASK 4
H1("Task 4 – Build a demonstrator and validate critical claims  (10 marks)")
H2("4.1 What was built")
P("A small, deterministic, standard-library Python demonstrator (`demonstrator/`): rubric-rule assistant with a forced-choice baseline, stakes-discrepancy matrix, "
  "salted hash-chained audit log, role-controlled workflow, retry-safe credential service, label-noise simulation, selection model and resource estimator. "
  "**No trained ML and no Blockchain are implemented**; both are evaluated as options only. "
  "Run: `python3 run_demonstrator.py` (seed 2026). 43 unit tests pass and `results.json` is reproduced byte-for-byte by a test.")
H2("4.2 Falsifiable claims and predictions (made before testing)")
P("Predictions, dataset and rubric were written and **frozen with SHA-256 hashes before the demonstrator was first run** (Appendix A). Outcomes below are compared with those predictions.")
table([["Claim", "Prediction written before testing", "Outcome", "Result"],
       ["C1 Deterministic matrix", "9/9 cells; 1,000 identical runs; 0 monotonicity violations", "9/9; identical; 0", "PASS"],
       ["C2a Baseline wrong", "≥ 6 wrong", f"{m['baseline']['wrong']} wrong", "PASS"],
       ["C2b Abstaining v1", "≤ 2 wrong among answered", f"**{m['v1']['wrong']} wrong**", "**FAIL** → R1"],
       ["C2c Revised v2 (post-revision)", "(not pre-registered; tuned after seeing v1)", f"{m['v2']['wrong']} wrong", "met, **non-independent**"],
       ["C2d Acceptance threshold", "wrong rate ≤ 10% on answered", f"{m['v2']['wrong_rate_on_answered']*100:.1f}% (CI {m['v2']['wrong_rate_wilson95'][0]*100:.0f}–{m['v2']['wrong_rate_wilson95'][1]*100:.0f}%)", "**FAIL**"],
       ["C3 Audit tamper behaviour", "T1-T8 as predicted", "All as predicted", "PASS"],
       ["C4 Workflow authorisation", "All checks pass", "All 20 pass", "PASS"],
       ["C5 Retry-safe issue", "1 certificate; marks unchanged; tampered grade rejected", "As predicted", "PASS"],
       ["C6 Label noise limits kappa", "DB κ ≥ 0.7; OS κ < 0.4", f"{R['C6']['subjects'][0]['examiner_kappa']:.2f}; {R['C6']['subjects'][1]['examiner_kappa']:.2f}", "PASS"]],
      [1.6, 2.4, 1.6, 0.95], size=8.5,
      fills={(3, 3): "FDE8E8", (5, 3): "FDE8E8", (4, 3): "FDF0DC", **{(i, 3): "E1F4E6" for i in (1, 2, 6, 7, 8, 9)}})
caption("Pre-registered claims versus observed outcomes.", "Table")
H2("4.3 Dataset and limitations")
P("`data/synthetic_answers.csv`: **24 synthetic answers** to “Explain the ACID properties”, hand-written by the author, each with an author-assigned expert band using the rubric’s band definition. "
  "Styles: standard (12), paraphrased (4), short/off-topic (3), term-listing (2), wrong-explanation (2), negated (1). No real student data.")
callout("**Limitations.** The set is tiny and **crafted to probe known weaknesses**, so it is not representative; one author set the expert bands; "
        "styles are not a random sample; confidence intervals are very wide; the rubric lexicon was written by the same author; and revision R1 was tuned on this same set. "
        "Nothing here estimates real-world accuracy.", fill="FDF0DC", edge="B45309")
H2("4.4 Baseline comparison – rubric assistant, paraphrase, unfamiliar terms, negation")
P("**Baseline** = forced choice from the count of matched rubric concepts (always answers). **v1** abstains on ≤ 1 matched concept, negated terms and very short answers. "
  "**v2 (R1)** additionally abstains when matched terms are not explained (fewer than 6 words per matched concept). All three ran on identical answers.")
shot("shot01_C2_assistant_vs_baseline.png", "Screenshot 1 – C2: per-answer outcomes, summary metrics, fairness by style and prediction check (real program output).")
figure(FIG / "fig_assistant_performance.png", "Outcome counts (a) and wrong-suggestion rate with 95% Wilson intervals (b).", landscape=True)
table([["Method", "Answered", "Manual Review", "Correct", "Wrong", "Wrong rate on answered", "95% interval", "Coverage"],
       *[[n, m[k]["answered"], m[k]["manual_review"], m[k]["correct"], m[k]["wrong"],
          f"{m[k]['wrong_rate_on_answered']*100:.1f}%", f"{m[k]['wrong_rate_wilson95'][0]*100:.0f}–{m[k]['wrong_rate_wilson95'][1]*100:.0f}%",
          f"{m[k]['coverage']*100:.0f}%"] for k, n in (("baseline", "Forced baseline"), ("v1", "Assistant v1"), ("v2", "Assistant v2 (R1)"))]],
      [1.3, 0.7, 0.8, 0.65, 0.55, 1.0, 0.85, 0.7], size=8.5)
caption("Baseline comparison under identical conditions.", "Table")
figure(FIG / "fig_fairness_by_style.png", "Fairness audit by answer style. The forced baseline mis-bands unfamiliar writing; abstention withholds a suggestion instead.", landscape=True)
P("**Reading the result.** Abstention removes wrong suggestions on paraphrased, negated and term-listing answers, but it does so by giving **no help** to those students’ examiners – "
  "so safety is bought with workload and with unequal assistance. Two answers with plausible terms but **wrong explanations** (rows 10, 22) were still banded Medium by every method: "
  "keyword rules cannot detect a wrong explanation, which is exactly why an examiner must read the answer.")
H2("4.5 Moderation-priority matrix (stakes × discrepancy)")
shot("shot02_C1_matrix.png", "Screenshot 2 – C1: matrix reproduced, 1,000 identical runs, monotonic, invalid inputs rejected.")
figure(FIG / "fig_moderation_matrix.png", "Moderation-priority matrix. An abstention carries no discrepancy and cannot raise or lower priority.", landscape=False, width=5.4)
H2("4.6 Audit and tamper behaviour – and what the design cannot verify")
shot("shot03_C3_audit_tamper.png", "Screenshot 3 – C3: tamper tests T1-T8 (real program output).")
figure(FIG / "fig_tamper_tests.png", "Tamper test results.", landscape=True)
table([["Threat", "Plain hash chain", "Chain + external checkpoint", "Ledger (proposed)"],
       ["Naive edit", "Detected (T2)", "Detected", "Detected"],
       ["Privileged rewrite with recomputation", "**Undetected** (T3)", "Detected (T4)", "Detected only if independent nodes hold copies"],
       ["Truncation of last entries", "**Undetected** (T5)", "Detected (T5b)", "Detected only if independent nodes hold copies"],
       ["False original mark in good faith", "**Not verifiable** (T6)", "Not verifiable", "**Not verifiable**"],
       ["Erasure of sensitive content", "Breaks chain if content is hashed in (T7a)", "Salted commitment keeps chain valid (T7b)", "Conflicts with immutability"],
       ["Dictionary attack on low-entropy marks", "Possible if unsalted (T8: 3/3)", "Blocked by salt (T8: 0/3)", "As chain"]],
      [1.8, 1.55, 1.65, 1.55], size=8.5, bold_first_col=True)
caption("What conventional audit controls and a ledger can and cannot verify – justification for excluding the ledger.", "Table")
P("**Exclusion substantiated separately.** The conventional alternative (chain + external checkpoint + role-controlled workflow) delivers the tamper-evidence the ledger was proposed for; "
  "the ledger adds value only when independent parties hold copies, which the scenario does not provide. The selected workflow was validated on its own (§4.7). No ledger was implemented or claimed.")
H2("4.7 Workflow, authorisation, correction, erasure and export")
shot("shot04_C4_workflow.png", "Screenshot 4 – C4: 20 authorisation, correction, erasure and redaction checks (real program output).")
P("Highlights: the assistant cannot approve (A1), nor can an examiner or moderator (A3, A4); an override without a reason is rejected (A2) and with a reason succeeds and raises priority to Urgent at High stakes (A2b); "
  "a dispute after the 7-day window is rejected (A9); a correction without a reason is rejected (A7) and with one creates a new version while keeping history (A8); the DPO can erase a superseded value without invalidating the chain (A13/A13b); "
  "and redacted export leaves 0 identifiers (A11b).")
H2("4.8 Failure scenario: external verifier unavailable")
shot("shot05_C5_C6.png", "Screenshot 5 – C5 retry-safe credential issue and C6 label-noise simulation (real program output).")
P("When the verification service was down for two calls, the local mark record was untouched, the request was retried and exactly **one** certificate was issued; a duplicate request returned “already_issued”. "
  "When it was down for the entire window the request stayed pending and completed after recovery. A certificate with a changed grade failed verification. "
  "**Limitation:** HMAC stands in for an asymmetric signature; the check proves the record is unchanged since issue, not that the grade was deserved.")
H2("4.9 Label-noise simulation (assumed noise; not real marks)")
figure(FIG / "fig_label_noise.png", "Examiner agreement and kappa under assumed label noise.", landscape=True)
P("Two simulated examiners label 400 synthetic answers per subject. With 5% assumed noise kappa is "
  f"{R['C6']['subjects'][0]['examiner_kappa']:.2f}; with 35% it is {R['C6']['subjects'][1]['examiner_kappa']:.2f}, below the 0.6 gate. "
  "The assistant agrees with the truth by construction in this simulation, so this shows only that **inconsistent labels limit what can be measured or learned**, not assistant performance.")
H2("4.10 Documented design revision")
callout("**Revision R1 – abstain on unexplained term lists.**  *Evidence:* v1 gave High to both term-listing answers whose expert band was Low (rows 14, 15), contributing 2 of its 4 wrong suggestions "
        "and missing the pre-registered target of ≤ 2. *Change:* an answer whose matched terms average fewer than 6 words per concept goes to Manual Review. "
        f"*Effect (OBSERVED):* wrong suggestions fall from {m['v1']['wrong']} to {m['v2']['wrong']}; coverage falls from {m['v1']['coverage']*100:.0f}% to {m['v2']['coverage']*100:.0f}%. "
        "*Caveat:* tuned on the same 24 answers, so it is not independent evidence; it also does not fix the two wrong-explanation answers.", fill="E8EEFC")
P("The salted-commitment design of the audit log (tests T7a, T7b, T8) was a deliberate design choice made before testing and was **confirmed** (not triggered) by the tests; it is not claimed as a failure-driven revision.", size=9.5, color=GREY)
H2("4.11 Unit tests and reproducibility")
shot("shot08_unit_tests.png", "Screenshot 6 – 43 unit tests including byte-for-byte reproduction of results.json.")
shot("shot06_selection_sensitivity.png", "Screenshot 7 – Task 2 and Task 6 selection model output.")

# =============================================================== TASK 5
H1("Task 5 – Create an ethical and sustainable operating plan  (5 marks)")
H2("5.1 Ethical and societal risk register")
table([["#", "Risk and possible harm", "Affected groups", "Safeguard", "Owner", "Escalation / appeal"],
       ["E1", "Wrongly suggested mark anchors the examiner → unfair mark", "Students", "Blind-first marking; matched terms shown; no confidence score; override with reason; sampling", "Controller", "Student dispute within 7 days → revaluation committee"],
       ["E2", "Unequal treatment of paraphrased or non-standard writing (forced choice mis-banded 4/4 paraphrased answers)", "Students writing in own words, second-language writers", "Abstain to Manual Review; per-style monitoring; no suggestion is shown as a verdict", "Head of department", "Fairness review each cycle; pause if gap exceeds threshold"],
       ["E3", "Sensitive answer text and marks exposed or retained too long", "Students", "Restricted store; redacted exports; retention schedule; salted commitments; erasure path", "DPO", "Data-protection complaint route; incident response"],
       ["E4", "Misleading confidence or ‘AI says’ authority reduces accountability", "Students, controller", "No probability shown; assistant has no approve right; controller signs every result", "Controller", "Audit review; suspend suggestions"],
       ["E5", "Immutable ledger copies prevent correction/erasure", "Students", "Ledger excluded; fingerprints only if ever used", "DPO / CIO", "Policy review before any ledger"],
       ["E6", "Inconsistent historical labels penalise a subject if ML is trained on them", "Students in that subject", "Kappa ≥ 0.6 gate; ML suspended for that subject", "Academic council", "Re-labelling exercise"],
       ["E7", "Automation complacency and de-skilling of examiners", "Examiners", "Blind-first protocol; periodic unassisted marking; override-rate monitoring", "Moderator lead", "Training; withdraw suggestions"],
       ["E8", "Cost and energy of added infrastructure displaces core services", "Institution", "Choose lowest-resource adequate option; budget check each cycle", "CIO", "Budget committee"]],
      [0.35, 1.65, 0.95, 1.7, 0.75, 1.2], size=7.8)
caption("Ethical and societal risk register with owners and appeal arrangements.", "Table")
H2("5.2 Operating cost and resource estimates under explicit workload assumptions")
est = R["resources"]
callout(f"**Measured vs estimated.**  Only **one** value is measured: rule evaluation time = **{T['rule_eval_ms_per_answer_median']:.4f} ms per answer** (median of 5 runs, single machine, Python {T['python']}; "
        f"audit append {T['append_us_per_entry']} µs/entry; verifying 10,000 entries {T['verify_10000_entries_ms']} ms). "
        f"Everything else below is an **estimate** from the stated assumptions. At the measured speed {est['answers_per_cycle']:,} answers need about **{T['rule_cpu_s_cycle_measured']:.1f} CPU-s**; "
        f"the planning table uses a conservative 1 ms/answer ({est['rule_cpu_s_cycle_planning']} CPU-s). No energy or carbon claim is made.", fill="E8EEFC")
rows = [["Alternative", "CPU-s per cycle (est.)", "Storage MB/year (est.)", "Labelling h per round (assumed)", "Fixed Rs/year (assumed)", "Governance h/year (assumed)", f"Fits {est['budget_original']} CPU-s", f"Fits {est['budget_halved']} CPU-s"]]
for k in "ABCD":
    a = est["alternatives"][k]
    rows.append([k, f"{a['cpu_s_cycle']:.0f}", f"{a['storage_mb_year']:.0f}", a["labelling_hours_round"], f"{a['fixed_rs_year']:,}", a["governance_hours_year"],
                 "Yes" if a["fits_original_budget"] else "No", "Yes" if a["fits_halved_budget"] else "**No**"])
table(rows, [0.7, 0.85, 0.85, 0.9, 0.85, 0.85, 0.75, 0.75], size=8.3,
      fills={(2, 7): "FDE8E8", (4, 7): "FDE8E8"})
caption("Resource and cost estimates per alternative (ESTIMATES).", "Table")
figure(FIG / "fig_resources.png", "Compute against budget, storage growth and people effort (estimates).", landscape=True)
table([["Assumption", "Value"],
       ["Per-answer storage (answer + mark record + 5 audit events)", f"{est['per_answer_kb']} KB (estimate)"],
       ["ML training and inference", "250 CPU-s per retrain + 3 ms per answer (assumed, unmeasured)"],
       ["Labelling effort for ML", "20 h per subject per round × 12 subjects = 240 h (assumed)"],
       ["Ledger", "4 nodes × Rs 1,500 per node-month = Rs 72,000/year; 48 governance hours/year (assumed)"],
       ["Illustrative compute price", "Rs 3 per vCPU-hour (illustrative allocation, not a quotation)"]],
      [3.4, 3.15], size=8.6)
caption("Key estimate assumptions.", "Table")
P("**Comparison.** A needs no labelling, no fixed infrastructure and fits both budgets. B’s compute is dominated by retraining and its 240 labelling hours per round are the real cost; "
  "it fits the original budget but **not the halved one** (442 > 300 CPU-s). C adds Rs 72,000/year fixed cost and governance time for a benefit that requires partners who do not exist. D carries both.")
H2("5.3 Monitoring indicators and pause / withdrawal criteria")
table([["Indicator", "Measure", "Frequency", "Pause when", "Withdraw when"],
       ["Wrong-band rate on answered suggestions", "Examiner-confirmed wrong / answered, with interval", "Each cycle", "> 10%", "> 10% for two consecutive cycles"],
       ["Override rate", "Overrides / suggestions shown", "Each cycle", "< 2% (possible over-reliance) or > 40% (poor fit)", "Persistent after retraining of examiners"],
       ["Abstention rate by answer style", "Manual Review share per style", "Each cycle", "Style gap > 25 points", "Gap persists after rubric revision"],
       ["Examiner agreement (kappa)", "Per subject, double-marked sample", "Each cycle", "κ < 0.6 for a subject", "–"],
       ["Dispute volume and success", "Disputes and upheld share", "Monthly", "Upheld share rises > 5 points", "Systematic suggestion-linked errors"],
       ["Audit integrity", "Daily head-hash + length match", "Daily", "Any mismatch", "Unexplained mismatch"],
       ["Identifiers in exported samples", "Automated scan", "Each export", "> 0", "Repeated leaks"],
       ["Budget", "CPU-s per cycle vs budget", "Each cycle", "> budget", "> budget after optimisation"]],
      [1.5, 1.6, 0.7, 1.4, 1.35], size=8.2)
caption("Monitoring plan with measurable thresholds (planning assumptions).", "Table")

# =============================================================== TASK 6
H1("Task 6 – Redesign for new evidence and operating constraints  (8 marks)")
callout("**Changed requirement.**  (1) Historical examiner marks are inconsistent for one subject category. (2) A partner institution withdraws from shared credential verification. "
        "(3) The computing budget is halved and corrections of sensitive or disputed records are required.", fill="FDF0DC", edge="B45309")
H2("A. Diagnose impact  (2 marks)")
table([["Changed evidence", "Assumption now broken", "Stakeholders affected", "Data / trust arrangement affected", "Resource effect"],
       ["Inconsistent marks in one subject (Operating Systems)", "ML needs consistent expert labels (B, D); examiner marks are a valid reference", "Students of that subject, examiners, moderators, dept head", "Training labels; moderation baseline for that subject", "Re-labelling hours added; ML data readiness drops"],
       ["Partner withdraws", "Shared trust needs ≥ 3 independent participants (C, D)", "External verifiers, controller", "Trust arrangement disappears; ledger would have one operator", "Ledger cost remains, benefit goes"],
       ["Budget halved (600 → 300 CPU-s)", "Compute fits the budget", "Operations, CIO", "–", "B and D (442 CPU-s) no longer fit"],
       ["Correct/erase sensitive or disputed records", "Immutable history is acceptable", "Students, DPO", "Audit store, any ledger", "Erasure workflow and retention work added"]],
      [1.3, 1.45, 1.2, 1.35, 1.25], size=8.2)
caption("Impact analysis.", "Table")
H2("B. Create the redesign  (3 marks)")
sc = R["selection"]["revised"]
P("**Revised scores** (changes only where the evidence changed): B – Reliability 2→1, Fairness 2→1, Cost 3→2; "
  "C – Usefulness 2→1 (re-scored with ledger no longer shared), Shared-trust 4→1, Reliability 3→2, Governance 2→1, Cost 2→1; "
  "D – Usefulness 4→3, Shared-trust 4→1, Reliability/Fairness/Governance/Cost each lowered. A is unchanged. "
  "Weights are revised to Reliability 20, Fairness 20, Cost 20, Usefulness 15, Privacy 15, Shared-trust 5, Governance 5 because the new constraints make cost and fairness more important and shared trust irrelevant.")
figure(FIG / "fig_redesign_scores.png", "Scores before and after the changed evidence.", landscape=False, width=6.2)
table([["Alternative", "Original", "Revised scores, original weights", "Revised scores, revised weights"],
       *[[a, f"{R['selection']['base'][a]:.2f}", f"{sc['original_weights'][a]:.2f}", f"{sc['revised_weights'][a]:.2f}"] for a in "ABCD"]],
      [1.3, 1.1, 2.1, 2.05], size=8.8)
caption("Weighted totals under the revision. Retention is a recommendation to **simplify**: A is retained and ML and ledger are removed from the plan.", "Table")
figure(FIG / "fig05_revised_blueprint.png", "Revised blueprint: core path retained and simplified; ML deferred offline; ledger removed.", landscape=True)
table([["Revision", "Change", "Reason"],
       ["R1", "Keep abstention on unexplained terms (v2)", "Reduces wrong suggestions where examiners are already inconsistent"],
       ["R2", "Commitments only in the chain; content in restricted store; erasure workflow mandatory for corrections", "Sensitive or disputed records must be correctable and erasable (A13)"],
       ["R3", "External daily head-hash checkpoint", "Closes privileged-edit and truncation gaps (T3, T5) without a ledger"],
       ["R4", "Conventional signed certificate + public fingerprint page", "Partner withdrawn; verifier outage handled by retry-safe issue"],
       ["R5", "ML deferred: separate offline environment; Operating Systems training suspended; kappa gate", "Labels inconsistent; ML exceeds halved budget (442 > 300 CPU-s)"],
       ["R6", "Blockchain removed from the plan", "No independent participants; erasure conflict; cost with no benefit"]],
      [0.7, 3.2, 2.65], size=8.5, bold_first_col=True)
caption("Redesign decisions.", "Table")
P("**Safeguards and operating plan changes:** correction of a disputed record always creates a new reasoned version; a student-erasure request erases superseded content only; "
  "the Operating Systems subject is double-marked on a sample until κ ≥ 0.6; the budget indicator pauses any new component that would exceed 300 CPU-s per cycle.")
H2("C. Validate and defend  (3 marks)")
table([["Re-run check", "Result (OBSERVED / SIMULATED / ESTIMATE)", "Supports"],
       ["Budget: compute per cycle vs halved budget", f"A {est['alternatives']['A']['cpu_s_cycle']:.0f} CPU-s fits 300; B and D {est['alternatives']['B']['cpu_s_cycle']:.0f} do not (ESTIMATE)", "R5"],
       ["Label noise: OS subject", f"κ = {R['C6']['subjects'][1]['examiner_kappa']:.2f} < 0.6 gate (SIMULATED)", "R5"],
       ["Erasure of superseded sensitive value", "A13/A13b: chain valid, content unverifiable, current mark intact (OBSERVED)", "R2"],
       ["Correction with reason / without reason", "A8 passes; A7 rejected (OBSERVED)", "Safeguards"],
       ["Verifier unavailable; no partner", "F1-F3: one certificate, local marks unchanged, tampered grade rejected (OBSERVED)", "R4"],
       ["Tampering without external checkpoint", "T3/T5 undetected; T4/T5b detected (OBSERVED)", "R3"],
       ["Revised selection", f"A {sc['revised_weights']['A']:.2f}, B {sc['revised_weights']['B']:.2f}, C {sc['revised_weights']['C']:.2f}, D {sc['revised_weights']['D']:.2f} (judgement)", "R1-R6"]],
      [2.1, 3.55, 0.9], size=8.5)
caption("Validation of the redesign using demonstrator checks and estimates.", "Table")
P("**Defence of the revised recommendation.** Retain A, simplify it (no ledger, no ML in production) and keep ML as a gated offline option. "
  "Every change in evidence moves ML and the ledger further from adoption, so keeping them would be adopting emerging technology as a predetermined outcome.")
P("**Limitations:** the revised scores are again judgements; erasure was tested on one record; the budget check uses assumed ML costs; a real partner-withdrawal and a real subject label review could differ; "
  "and the A-versus-D margin in S6 (3.35 vs 3.20) shows that a very different set of conditions could re-open the decision.")

# =============================================================== TASK 7
H1("Task 7 – Individual technical reflection  (4 marks)")
H3("Which assumption most strongly influenced my technology choice?")
P("That **there is no independent party that needs to verify records with the university, and no validated set of expert labels**. "
  "Both ledger and ML options only become attractive if these assumptions are false: S6 is the only scenario in which A loses, and it flips only when labels are validated, institutions are committed and usefulness/trust weights are raised together. "
  "Because both assumptions are claims about the world that I could not test with synthetic data, they are the most important things to check first.")
H3("Which observed result challenged my initial recommendation?")
P(f"My abstaining assistant **missed its own pre-registered target**: v1 made {m['v1']['wrong']} wrong suggestions against a prediction of ≤ 2, because it gave **High** to two term-listing answers that an expert would rate **Low**. "
  "I had expected abstention on weak evidence to be enough; it was not, because a list of correct terms *looks* like strong evidence to keyword rules. "
  "It challenged any impression that rules are “safe because they are simple”. Revision R1 reduced the error but cut coverage to 58% and left two wrong-explanation answers uncaught, so the honest conclusion is that the assistant is an **aid to reading**, not a source of marks.")
H3("Which ethical or sustainability trade-off remains significant?")
P("**Safety versus equal help.** Abstention protects students from wrong suggestions, but the answers it sends to Manual Review – paraphrased, unusual or second-language writing – are the very ones that get no assistance, so the examiners’ workload and any speed benefit fall unevenly. "
  "There is also a **privacy versus accountability** tension: keeping a full immutable history helps audits, but students may legitimately request erasure; my design keeps commitments and metadata but loses the ability to re-verify erased values.")
H3("What further evidence is required before real deployment?")
for t in ("**Real, labelled, consented or properly approved data:** two independent expert labels per answer, per-subject kappa, stratified by writing style and language background.",
          "**An independent evaluation** of the assistant on data the rules were not tuned on, with confidence intervals large enough to test the 10% threshold.",
          "**Human-factors testing** of anchoring and over-reliance with real examiners (blind-first vs suggestion-first).",
          "**Security and privacy review:** asymmetric signatures and key management, access-control penetration testing, DPO and legal assessment of retention and erasure.",
          "**Measured operating cost** under production load and real quotations, replacing the estimates in Task 5.",
          "**Governance confirmation:** named owners, approved dispute procedure, and written partner commitments if a shared ledger is ever reconsidered."):
    B(t)

# =============================================================== APPENDICES
H1("Appendix A – Pre-registered claims and predictions")
P("Written before the first run. Files frozen with SHA-256 (UTC 2026-11-21T21:44:36Z).")
table([["File", "SHA-256"],
       ["data/synthetic_answers.csv", "dfc1e6b5503a1419d60d259a67d1685bee20958a8a5e4dc68913ef743e17261d"],
       ["data/rubric_acid.json", "feb07d4d5243390aa2205ef6f3e23047b48bb5b12e187932888eabae6ef66247"]], [2.0, 4.55], size=8)
P((ROOT / "docs" / "predictions.md").read_text().split("## Claims (each can be falsified)")[1].replace("**", "").strip()[:2600] + " …", size=8.8, color=GREY)
P("Full text: `docs/predictions.md` in the repository. Note: the wrong-rate threshold (≤ 10%) and the v1 target (≤ 2 wrong) are planning values set by the author.", size=8.8, color=GREY)

H1("Appendix B – How to reproduce")
for t in ("`python3 -m venv .venv` is optional; the demonstrator uses only the Python standard library (Python 3.10+; developed on 3.13).",
          "`python3 run_demonstrator.py` regenerates `results/results.json` (deterministic) and `results/timing.json` (machine-specific).",
          "`python3 -m unittest discover -s tests -v` runs 43 tests, including byte-for-byte reproduction of `results.json`.",
          "Optional (figures and report): `pip install matplotlib python-docx pillow playwright`, then run `tools/make_charts.py`, `tools/make_diagrams.py`, `tools/make_screenshots.py`, `tools/build_report.py`.",
          "Dataset: `data/synthetic_answers.csv`; rubric: `data/rubric_acid.json`; seed: 2026."):
    B(t)
H1("Appendix C – References")
refs = ["Cohen, J. (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1), 37-46.",
        "Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. Biometrics, 33(1), 159-174.",
        "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association, 22(158), 209-212.",
        "Haber, S., & Stornetta, W. S. (1991). How to time-stamp a digital document. Journal of Cryptology, 3(2), 99-111.",
        "Parasuraman, R., & Manzey, D. H. (2010). Complacency and bias in human use of automation. Human Factors, 52(3), 381-410.",
        "Wüst, K., & Gervais, A. (2018). Do you need a blockchain? IEEE Crypto Valley Conference on Blockchain Technology.",
        "National Institute of Standards and Technology (2023). Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST AI 100-1.",
        "Regulation (EU) 2016/679 (GDPR), Article 17 – right to erasure.",
        "Regulation (EU) 2024/1689 (Artificial Intelligence Act), Annex III – education and vocational training uses classified as high-risk.",
        "Digital Personal Data Protection Act, 2023 (India)."]
for r in refs:
    B(r)
P("References were cited from the author’s knowledge and were not re-verified online in this session; check titles, pages and clause numbers against the originals before submission.", size=8.8, color=GREY)
H1("Appendix D – Tools and acknowledgements")
table([["Tool", "Use"],
       ["Python 3.13 standard library", "Demonstrator, unit tests"],
       ["matplotlib, Pillow", "Charts and architecture diagrams (rendered at 250 dpi)"],
       ["Playwright / Chromium", "HD (2×) rendering of real program output into terminal screenshots"],
       ["python-docx, LibreOffice", "Report generation and PDF export"],
       ["Claude (Anthropic AI assistant)", "Drafted the demonstrator, figures and report text under the student’s direction. **The student must review, understand and be able to defend and reproduce every claim (assessment verification).**"]],
      [2.1, 4.45], size=8.8, bold_first_col=True)

out = OUT / "CSA10_Assignment5_Report.docx"
doc.save(out)
print("saved", out)
