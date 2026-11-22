"""Weighted decision matrix, sensitivity analysis and redesign re-scoring.

All scores (1-5 ordinal) are reasoned planning judgements linked to evidence in
the report, NOT experimental measurements. Weighted score = sum(weight*score)/100.
"""
ALTS = {"A": "Rules + human evaluation (conventional)",
        "B": "Trained ML scoring assistance",
        "C": "Blockchain shared credential verification",
        "D": "Combined ML + Blockchain"}

CRITERIA = ["Usefulness", "Shared-trust need", "Reliability", "Privacy", "Fairness",
            "Cost sustainability", "Governance readiness"]

W0 = {"Usefulness": 15, "Shared-trust need": 10, "Reliability": 20, "Privacy": 15,
      "Fairness": 15, "Cost sustainability": 15, "Governance readiness": 10}

S0 = {
    "A": {"Usefulness": 3, "Shared-trust need": 2, "Reliability": 4, "Privacy": 5,
          "Fairness": 3, "Cost sustainability": 5, "Governance readiness": 5},
    "B": {"Usefulness": 4, "Shared-trust need": 1, "Reliability": 2, "Privacy": 3,
          "Fairness": 2, "Cost sustainability": 3, "Governance readiness": 1},
    "C": {"Usefulness": 1, "Shared-trust need": 4, "Reliability": 3, "Privacy": 2,
          "Fairness": 3, "Cost sustainability": 2, "Governance readiness": 2},
    "D": {"Usefulness": 4, "Shared-trust need": 4, "Reliability": 2, "Privacy": 2,
          "Fairness": 2, "Cost sustainability": 1, "Governance readiness": 1},
}

EVIDENCE = {
    "Usefulness": "Help with timely, consistent evaluation. A: highlights rubric terms and flags discrepancy; "
                  "suggests on a subset only (coverage measured in the demonstrator). B: wider semantic coverage if labels exist (not demonstrated). "
                  "C: no help with evaluation. D: as B.",
    "Shared-trust need": "How well the option serves several institutions that must verify credentials. A: one issuer, signed certificate + "
                         "verification page. B: none. C/D: designed for independent verifiers, but only if they exist.",
    "Reliability": "Wrong-band risk and safe failure. A: abstention and safe failure observed in the demonstrator. B: no validated labels; "
                   "scores uncalibrated. C: protects record integrity, not truth of input (T6). D: inherits B and C limits.",
    "Privacy": "A: content stays in restricted store; only commitments leave it. B: training copies of answers. "
               "C/D: immutable copies conflict with erasure (T7a).",
    "Fairness": "Equal treatment of writing styles. A: forced choice mistreated paraphrased answers; abstention removes wrong suggestions "
                "but gives them no help. B: unknown, learns label noise. C: neutral. D: as B.",
    "Cost sustainability": "A: rule time measured; B: retraining and labelling (estimates). C: nodes and governance (estimates). D: both.",
    "Governance readiness": "A: owners and workflow exist. B: no expert labels yet. C: partner institutions not committed. D: both missing.",
}


def weighted(scores, weights):
    return round(sum(weights[c] * scores[c] for c in CRITERIA) / 100, 2)


def table(scores, weights):
    return {a: weighted(scores[a], weights) for a in scores}


def with_overrides(scores, overrides):
    new = {a: dict(s) for a, s in scores.items()}
    for a, o in overrides.items():
        new[a].update(o)
    return new


_S2 = {"B": {"Reliability": 3, "Fairness": 3, "Governance readiness": 4},
       "D": {"Reliability": 3, "Fairness": 3, "Governance readiness": 2}}
_S3 = {"C": {"Governance readiness": 4}, "D": {"Governance readiness": 2}}


def _merge(*ovs):
    out = {}
    for o in ovs:
        for a, d in o.items():
            out.setdefault(a, {}).update(d)
    return out


SENS = {
    "Base": (W0, {}),
    "S1 usefulness-heavy weights": (
        {"Usefulness": 30, "Shared-trust need": 10, "Reliability": 15, "Privacy": 10,
         "Fairness": 10, "Cost sustainability": 15, "Governance readiness": 10}, {}),
    "S2 validated labels exist": (W0, _S2),
    "S3 four institutions committed": (
        {"Usefulness": 10, "Shared-trust need": 25, "Reliability": 15, "Privacy": 15,
         "Fairness": 10, "Cost sustainability": 15, "Governance readiness": 10}, _S3),
    "S4 cost and privacy deprioritised": (
        {"Usefulness": 25, "Shared-trust need": 10, "Reliability": 25, "Privacy": 5,
         "Fairness": 20, "Cost sustainability": 5, "Governance readiness": 10}, {}),
    "S5 labels exist + usefulness-heavy": (
        {"Usefulness": 40, "Shared-trust need": 5, "Reliability": 15, "Privacy": 10,
         "Fairness": 10, "Cost sustainability": 10, "Governance readiness": 10}, _S2),
    "S6 labels + institutions + usefulness/trust-heavy": (
        {"Usefulness": 30, "Shared-trust need": 30, "Reliability": 10, "Privacy": 10,
         "Fairness": 10, "Cost sustainability": 5, "Governance readiness": 5},
        _merge(_S2, _S3)),
}


def sensitivity():
    out = {}
    for name, (w, ov) in SENS.items():
        assert sum(w.values()) == 100, name
        out[name] = table(with_overrides(S0, ov), w)
    return out


def sweep(criterion, scores=S0, step=1, weights0=W0):
    """Raise one criterion's weight to w; scale the others proportionally."""
    others = [c for c in CRITERIA if c != criterion]
    base_other = sum(weights0[c] for c in others)
    curve = {a: [] for a in scores}
    ws = list(range(0, 91, step))
    for w in ws:
        weights = {c: weights0[c] * (100 - w) / base_other for c in others}
        weights[criterion] = w
        for a in scores:
            curve[a].append(round(sum(weights[c] * scores[a][c] for c in CRITERIA) / 100, 3))
    be = {}
    for a in ("B", "C", "D"):
        be[a] = next((w for w, sa, sb in zip(ws, curve[a], curve["A"]) if sa > sb), None)
    return {"criterion": criterion, "weights": ws, "curve": curve, "break_even_vs_A": be}


def break_evens():
    s2 = with_overrides(S0, _S2)
    s23 = with_overrides(S0, _merge(_S2, _S3))
    return {
        "usefulness_base": sweep("Usefulness", S0)["break_even_vs_A"],
        "usefulness_labels_validated": sweep("Usefulness", s2)["break_even_vs_A"],
        "shared_trust_base": sweep("Shared-trust need", S0)["break_even_vs_A"],
        "shared_trust_institutions_committed": sweep("Shared-trust need", with_overrides(S0, _S3))["break_even_vs_A"],
        "shared_trust_both_conditions": sweep("Shared-trust need", s23)["break_even_vs_A"],
    }


# ---- Changed requirement (Task 6) -------------------------------------------
REVISED_OVERRIDES = {
    "B": {"Reliability": 1, "Fairness": 1, "Cost sustainability": 2},
    "C": {"Usefulness": 1, "Shared-trust need": 1, "Reliability": 2,
          "Governance readiness": 1, "Cost sustainability": 1},
    "D": {"Usefulness": 3, "Shared-trust need": 1, "Reliability": 1, "Fairness": 1,
          "Governance readiness": 1, "Cost sustainability": 1},
}
W_REVISED = {"Usefulness": 15, "Shared-trust need": 5, "Reliability": 20, "Privacy": 15,
             "Fairness": 20, "Cost sustainability": 20, "Governance readiness": 5}


def revised():
    s1 = with_overrides(S0, REVISED_OVERRIDES)
    assert sum(W_REVISED.values()) == 100
    return {"scores": s1,
            "original_weights": table(s1, W0),
            "revised_weights": table(s1, W_REVISED)}
