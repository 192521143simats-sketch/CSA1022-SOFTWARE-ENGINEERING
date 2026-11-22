"""Labelled label-noise simulation (assumed noise, synthetic data, no real marks).

Each synthetic answer has a TRUE band derived from how many rubric concepts it
contains. The rule assistant reads those concepts, so it matches the true band
BY CONSTRUCTION - this is not performance evidence. The point is to show how
examiner label noise alone changes measured agreement and kappa.
"""
import random

from . import BANDS, SEED


def true_band_from_concepts(k):
    return "High" if k >= 3 else "Medium" if k == 2 else "Low"


def noisy_label(rng, true, noise):
    if rng.random() >= noise:
        return true
    return rng.choice([b for b in BANDS if b != true])


def cohen_kappa(a, b, labels=BANDS):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in labels)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def simulate_subject(name, noise, n=400, seed=SEED):
    rng = random.Random(f"{seed}-{name}")
    true, e1, e2, assistant = [], [], [], []
    for _ in range(n):
        k = rng.choices([0, 1, 2, 3, 4], weights=[10, 20, 25, 25, 20])[0]
        t = true_band_from_concepts(k)
        true.append(t)
        e1.append(noisy_label(rng, t, noise))
        e2.append(noisy_label(rng, t, noise))
        assistant.append(t)                       # by construction
    agree = sum(x == y for x, y in zip(e1, e2)) / n
    return {
        "subject": name, "n": n, "assumed_noise": noise,
        "examiner_agreement": round(agree, 3),
        "examiner_kappa": round(cohen_kappa(e1, e2), 3),
        "assistant_vs_examiner1": round(sum(x == y for x, y in zip(assistant, e1)) / n, 3),
        "assistant_vs_true": round(sum(x == y for x, y in zip(assistant, true)) / n, 3),
    }


def run(kappa_gate=0.6):
    subjects = [simulate_subject("Databases", 0.05), simulate_subject("Operating Systems", 0.35)]
    for s in subjects:
        s["passes_kappa_gate"] = s["examiner_kappa"] >= kappa_gate
    return {"kappa_gate": kappa_gate, "subjects": subjects}
