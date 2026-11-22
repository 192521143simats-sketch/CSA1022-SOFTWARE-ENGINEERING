"""Deterministic rubric-rule assistant (NOT a trained model).

Three versions are compared on identical inputs:
  baseline : forced choice, counts matched rubric concepts, no abstention
  v1       : abstains on <=1 matched concept, negated terms, very short answers
  v2 (R1)  : v1 plus abstains when matched terms are not explained
             (fewer than MIN_WORDS_PER_CONCEPT words per matched concept)
"""
import csv
import json
import re
from pathlib import Path

from . import MANUAL

ROOT = Path(__file__).resolve().parent.parent
MIN_WORDS_TOTAL = 6            # v1: shorter answers abstain
MIN_WORDS_PER_CONCEPT = 6      # v2 (revision R1): term lists abstain
NEG_WINDOW = 4                 # tokens between a negation pattern and a matched term


def load_rubric(path=None):
    path = Path(path) if path else ROOT / "data" / "rubric_acid.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_answers(path=None):
    path = Path(path) if path else ROOT / "data" / "synthetic_answers.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["id"] = int(r["id"])
    return rows


def tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def _concept_positions(toks, keywords):
    """Token indices where any keyword (stem or phrase) starts."""
    pos = []
    for kw in keywords:
        kt = re.findall(r"[a-z]+", kw.lower())
        n = len(kt)
        for i in range(len(toks) - n + 1):
            window = toks[i:i + n]
            if n == 1:
                if window[0].startswith(kt[0]):
                    pos.append(i)
            elif window == kt:
                pos.append(i)
    return sorted(set(pos))


def matched_concepts(text, rubric):
    toks = tokens(text)
    found = {}
    for concept, kws in rubric["concepts"].items():
        p = _concept_positions(toks, kws)
        if p:
            found[concept] = p
    return found


def has_negated_term(text, rubric, found=None):
    """True if a negation pattern sits within NEG_WINDOW tokens of a matched term."""
    toks = tokens(text)
    found = found if found is not None else matched_concepts(text, rubric)
    term_pos = [i for plist in found.values() for i in plist]
    for pat in rubric["negation_patterns"]:
        pt = re.findall(r"[a-z]+", pat)
        n = len(pt)
        for i in range(len(toks) - n + 1):
            if toks[i:i + n] == pt:
                if any(abs(i - tp) <= NEG_WINDOW for tp in term_pos):
                    return True
    return False


def band_from_count(k):
    return "High" if k >= 3 else "Medium" if k == 2 else "Low"


def baseline(text, rubric):
    """Forced-choice baseline: always returns a band."""
    k = len(matched_concepts(text, rubric))
    return {"band": band_from_count(k), "matched": k, "reason": "forced"}


def assist(text, rubric, version="v2"):
    """Abstaining assistant. Returns band or MANUAL with the abstention reason."""
    if version not in ("v1", "v2"):
        raise ValueError("version must be 'v1' or 'v2'")
    found = matched_concepts(text, rubric)
    k = len(found)
    words = len(tokens(text))
    if k <= 1:
        return {"band": MANUAL, "matched": k, "reason": "insufficient_evidence"}
    if has_negated_term(text, rubric, found):
        return {"band": MANUAL, "matched": k, "reason": "negated_term"}
    if words < MIN_WORDS_TOTAL:
        return {"band": MANUAL, "matched": k, "reason": "too_short"}
    if version == "v2" and words / k < MIN_WORDS_PER_CONCEPT:
        return {"band": MANUAL, "matched": k, "reason": "unexplained_terms"}
    return {"band": band_from_count(k), "matched": k, "reason": "rules"}
