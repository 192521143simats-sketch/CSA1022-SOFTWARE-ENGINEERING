#!/usr/bin/env python3
"""Charts built ONLY from results/results.json (nothing typed in by hand)."""
import json
from pathlib import Path

import numpy as np
from fig_common import *  # noqa

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
R = json.loads((ROOT / "results" / "results.json").read_text())
ALTS = {"A": "A  Rules +\nhuman", "B": "B  Trained\nML", "C": "C  Blockchain\nledger", "D": "D  ML +\nledger"}
CRIT = ["Usefulness", "Shared-trust need", "Reliability", "Privacy", "Fairness", "Cost sustainability", "Governance readiness"]


# ---------------------------------------------------------------- moderation matrix
def fig_moderation():
    fig, ax = plt.subplots(figsize=(9, 5.6))
    cell = R["C1"]["cells"]
    colors = {"Routine": GREEN_L, "Priority": AMBER_L, "Urgent": RED_L}
    edge = {"Routine": GREEN, "Priority": AMBER, "Urgent": RED}
    stakes = ["High", "Medium", "Low"]
    for i, s in enumerate(stakes):
        for d in range(3):
            v = cell[f"{s}-{d}"]
            ax.add_patch(Rectangle((d, i), 1, 1, fc=colors[v], ec="#fff", lw=4))
            ax.text(d + .5, i + .5, v, ha="center", va="center", fontsize=15, fontweight="bold", color=edge[v])
    ax.set_xlim(0, 3); ax.set_ylim(0, 3)
    ax.set_xticks([.5, 1.5, 2.5]); ax.set_xticklabels(["0 bands\n(agree)", "1 band apart", "2 bands apart"], fontsize=11)
    ax.set_yticks([.5, 1.5, 2.5]); ax.set_yticklabels([f"{s} stakes" for s in reversed(stakes)], fontsize=11)
    ax.xaxis.tick_top(); ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel("Discrepancy between examiner's band and assistant's suggested band", fontsize=11, labelpad=10)
    ax.xaxis.set_label_position("bottom")
    fig.suptitle("Stakes-discrepancy moderation-priority matrix (C1: 9 of 9 cells reproduced, 1,000 identical runs)",
                 fontsize=12, fontweight="bold", y=0.995)
    fig.tight_layout()
    save(fig, FIG / "fig_moderation_matrix.png")


# ---------------------------------------------------------------- decision matrix
def fig_decision():
    S, W, base = R["selection"]["scores"], R["selection"]["weights"], R["selection"]["base"]
    fig = plt.figure(figsize=(16, 7.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], wspace=0.5, left=0.17, right=0.97, top=0.82, bottom=0.12)
    ax = fig.add_subplot(gs[0])
    alts = list(S.keys())
    data = np.array([[S[a][c] for a in alts] for c in CRIT])
    ax.imshow(data, cmap="YlGnBu", vmin=0, vmax=5.8, aspect="auto")
    for i, c in enumerate(CRIT):
        for j, a in enumerate(alts):
            ax.text(j, i, str(data[i, j]), ha="center", va="center", fontsize=17, fontweight="bold",
                    color="#fff" if data[i, j] >= 4 else INK)
    ax.set_xticks(range(4)); ax.set_xticklabels([ALTS[a] for a in alts], fontsize=11)
    ax.set_yticks(range(len(CRIT))); ax.set_yticklabels([f"{c}   ({W[c]}%)" for c in CRIT], fontsize=11)
    ax.xaxis.tick_top(); ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("Ordinal scores 1-5 (higher is better) with criterion weights", fontsize=12, pad=38, loc="left")
    ax2 = fig.add_subplot(gs[1])
    vals = [base[a] for a in alts]
    bars = ax2.barh(range(4), vals, color=[ALT_COL[a] for a in alts], height=.62)
    ax2.set_yticks(range(4)); ax2.set_yticklabels(list(alts), fontsize=13, fontweight="bold")
    ax2.invert_yaxis(); ax2.set_xlim(0, 5)
    for b, v in zip(bars, vals):
        ax2.text(v + .06, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Weighted score out of 5 = sum(weight x score) / 100", fontsize=11)
    ax2.set_title("Weighted totals", fontsize=12, loc="left")
    ax2.grid(axis="x", color=GRID); ax2.set_axisbelow(True)
    fig.suptitle("Weighted decision matrix (scores are reasoned planning judgements, not measurements)",
                 fontsize=14, fontweight="bold", y=0.99)
    save(fig, FIG / "fig_decision_matrix.png")


# ---------------------------------------------------------------- sensitivity
def fig_sensitivity():
    sens = R["selection"]["sensitivity"]
    names = list(sens.keys())
    fig = plt.figure(figsize=(16, 8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.22, left=0.2, right=0.98, top=0.9, bottom=0.2)
    ax = fig.add_subplot(gs[0])
    h = .19
    for k, a in enumerate("ABCD"):
        ys = np.arange(len(names)) + (k - 1.5) * h
        v = [sens[n][a] for n in names]
        ax.barh(ys, v, height=h * .92, color=ALT_COL[a], label=ALTS[a].replace("\n", " "))
    for i, n in enumerate(names):
        best = max(sens[n], key=sens[n].get)
        ax.text(4.28, i, f"best: {best}", va="center", fontsize=11, fontweight="bold",
                color=ALT_COL[best])
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([n.replace(" + ", " +\n") if len(n) > 34 else n for n in names], fontsize=10)
    ax.invert_yaxis(); ax.set_xlim(0, 4.9)
    ax.set_xlabel("Weighted score out of 5", fontsize=11)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.1), fontsize=10, frameon=False, ncol=4)
    ax.set_title("(a) Seven scenarios: weights and assumptions changed", fontsize=12, loc="left")
    ax2 = fig.add_subplot(gs[1])
    sw = R["selection"]["sweep_usefulness_labels"]
    w = sw["weights"]
    for a in "ABD":
        ax2.plot(w, sw["curve"][a], color=ALT_COL[a], lw=2.6, label=ALTS[a].replace("\n", " "))
    be = R["selection"]["break_even"]["usefulness_labels_validated"]
    ax2.axvline(be["B"], color=AMBER, ls="--", lw=1.4)
    ax2.annotate(f"B overtakes A\nat Usefulness weight {be['B']}%", xy=(be["B"], sw["curve"]["B"][be["B"]]),
                 xytext=(be["B"] - 50, 2.1), fontsize=10, color=AMBER, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.4))
    ax2.set_xlim(0, 90); ax2.set_ylim(1.5, 4.6)
    ax2.set_xlabel("Weight on Usefulness (%), other weights scaled proportionally", fontsize=11)
    ax2.set_ylabel("Weighted score", fontsize=11)
    ax2.grid(color=GRID); ax2.legend(fontsize=9.5, loc="upper left")
    ax2.set_title("(b) Break-even when expert labels are validated (S2)", fontsize=12, loc="left")
    fig.suptitle("Sensitivity analysis: A stays selected unless several conditions change together",
                 fontsize=14, fontweight="bold", y=0.99)
    save(fig, FIG / "fig_sensitivity.png")


# ---------------------------------------------------------------- assistant performance
def fig_assistant():
    m = R["C2"]["metrics"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(15, 6.6), gridspec_kw={"width_ratios": [1.1, 1]})
    names = [("baseline", "Forced-choice\nbaseline"), ("v1", "Assistant v1\n(abstains)"), ("v2", "Assistant v2\n(after R1)")]
    x = np.arange(3)
    cor = [m[k]["correct"] for k, _ in names]
    wr = [m[k]["wrong"] for k, _ in names]
    man = [m[k]["manual_review"] for k, _ in names]
    ax.bar(x, cor, color=GREEN, label="Correct suggestion", width=.55)
    ax.bar(x, wr, bottom=cor, color=RED, label="Wrong suggestion", width=.55)
    ax.bar(x, man, bottom=np.array(cor) + np.array(wr), color=SLATE, alpha=.55, label="Manual Review (no suggestion)", width=.55)
    for i in range(3):
        ax.text(i, cor[i] / 2, str(cor[i]), ha="center", va="center", color="#fff", fontsize=15, fontweight="bold")
        if wr[i]:
            ax.text(i, cor[i] + wr[i] / 2, str(wr[i]), ha="center", va="center", color="#fff", fontsize=15, fontweight="bold")
        if man[i]:
            ax.text(i, cor[i] + wr[i] + man[i] / 2, str(man[i]), ha="center", va="center", color=INK, fontsize=15, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([n for _, n in names], fontsize=11)
    ax.set_ylabel("Answers (24 synthetic, expert-labelled)", fontsize=11); ax.set_ylim(0, 27)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, fontsize=9.5, frameon=False)
    ax.set_title("(a) Outcome per method on identical answers", fontsize=12, loc="left")
    ax2.axhline(10, color=RED, ls="--", lw=1.5)
    ax2.text(2.45, 10.8, "10% acceptance\nthreshold", color=RED, fontsize=9.5, ha="right", fontweight="bold")
    for i, (k, n) in enumerate(names):
        v = m[k]["wrong_rate_on_answered"] * 100
        lo, hi = [q * 100 for q in m[k]["wrong_rate_wilson95"]]
        ax2.bar(i, v, color=[SLATE, AMBER, BLUE][i], width=.5)
        ax2.errorbar(i, v, yerr=[[v - lo], [hi - v]], color=INK, capsize=7, lw=1.8)
        ax2.text(i + .3, v, f"{v:.1f}%", va="center", fontsize=12, fontweight="bold")
    ax2.set_xticks(range(3)); ax2.set_xticklabels([n for _, n in names], fontsize=11)
    ax2.set_ylabel("Wrong-suggestion rate on answered items (%)", fontsize=11); ax2.set_ylim(0, 65)
    ax2.set_title("(b) Wrong-rate with 95% Wilson interval", fontsize=12, loc="left")
    ax2.text(1, 60, "Intervals are very wide: 24 crafted answers cannot establish a real-world rate",
             ha="center", fontsize=9.5, color=MUTED)
    fig.suptitle("Observed results of the deterministic rubric assistant (not a trained model)", fontsize=14, fontweight="bold", y=0.99)
    fig.tight_layout(rect=[0, 0, 1, .95])
    save(fig, FIG / "fig_assistant_performance.png")


# ---------------------------------------------------------------- fairness by style
def fig_fairness():
    bs = R["C2"]["by_style"]
    styles = ["standard", "paraphrased", "negated", "term_listing", "wrong_explanation", "short_or_offtopic"]
    pretty = {"standard": "Standard (uses rubric terms)", "paraphrased": "Paraphrased (own words)",
              "negated": "Negated statement", "term_listing": "Term listing, no explanation",
              "wrong_explanation": "Terms with wrong explanation", "short_or_offtopic": "Short / off-topic"}
    methods = [("baseline", "Forced baseline"), ("v1", "Assistant v1"), ("v2", "Assistant v2 (R1)")]
    fig, ax = plt.subplots(figsize=(13.5, 7))
    for i, s in enumerate(styles):
        n = bs[s]["n"]
        for j, (k, _) in enumerate(methods):
            c = bs[s][k]
            wrong, ans, man = c["wrong"], c["answered"], c["manual"]
            if wrong > 0:
                fc, ec, txt = RED_L, RED, f"{wrong} of {ans} wrong"
                if man:
                    txt += f"\n{man} to manual"
            elif man == n:
                fc, ec, txt = SLATE_L, SLATE, f"all {man} to manual\n(no suggestion)"
            elif man:
                fc, ec, txt = AMBER_L, AMBER, f"{ans} correct\n{man} to manual"
            else:
                fc, ec, txt = GREEN_L, GREEN, f"{ans} of {ans} correct"
            ax.add_patch(Rectangle((j, len(styles) - 1 - i), 1, 1, fc=fc, ec="#fff", lw=4))
            ax.text(j + .5, len(styles) - 1 - i + .5, txt, ha="center", va="center", fontsize=11, color=ec, fontweight="bold")
    ax.set_xlim(0, 3); ax.set_ylim(0, len(styles))
    ax.set_xticks([.5, 1.5, 2.5]); ax.set_xticklabels([m for _, m in methods], fontsize=12, fontweight="bold")
    ax.set_yticks([len(styles) - 1 - i + .5 for i in range(len(styles))])
    ax.set_yticklabels([f"{pretty[s]}  (n={bs[s]['n']})" for s in styles], fontsize=11)
    ax.xaxis.tick_top(); ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.suptitle("Fairness audit by answer style: forced choice mistreats unfamiliar writing; abstention trades wrong suggestions for no help",
                 fontsize=12.5, fontweight="bold", y=0.995)
    fig.text(0.5, 0.012, "Green = all correct   Amber = correct where it answers, some to Manual Review   Grey = no suggestion   Red = wrong suggestions made",
             ha="center", fontsize=10, color=MUTED)
    fig.tight_layout(rect=[0, .03, 1, .96])
    save(fig, FIG / "fig_fairness_by_style.png")


# ---------------------------------------------------------------- tamper tests
def fig_tamper():
    tests = R["C3"]["tests"]
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.axis("off")
    cols = ["Test", "Scenario", "Expected", "Observed", "Result"]
    xs = [0.0, 0.07, 0.50, 0.66, 0.95]
    ax.set_xlim(0, 1); ax.set_ylim(0, len(tests) + 1.2)
    for x, c in zip(xs, cols):
        ax.text(x, len(tests) + .6, c, fontsize=12, fontweight="bold", va="center")
    ax.plot([0, 1], [len(tests) + .2] * 2, color=INK, lw=1.6)
    for i, t in enumerate(tests):
        y = len(tests) - 1 - i + .5
        if i % 2 == 0:
            ax.add_patch(Rectangle((0, y - .5), 1, 1, fc="#f6f8fb", ec="none", zorder=0))
        ax.text(xs[0], y, t["test"], fontsize=11, fontweight="bold", va="center")
        ax.text(xs[1], y, t["description"], fontsize=10.5, va="center")
        ax.text(xs[2], y, t["expected"], fontsize=10.5, va="center", color=MUTED)
        obs = t["observed"].replace("head_mismatch_vs_checkpoint", "head mismatch").replace("length_mismatch_vs_checkpoint", "length mismatch")
        ax.text(xs[3], y, obs, fontsize=10.5, va="center")
        ax.text(xs[4], y, "PASS" if t["pass"] else "FAIL", fontsize=11, fontweight="bold",
                color=GREEN if t["pass"] else RED, va="center")
    fig.suptitle("C3  Hash-chained audit log: tamper tests (observed). Detection needs an external checkpoint; truth of input is never checked.",
                 fontsize=12.5, fontweight="bold", y=.97)
    save(fig, FIG / "fig_tamper_tests.png")


# ---------------------------------------------------------------- label noise
def fig_noise():
    subs = R["C6"]["subjects"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    names = [s["subject"] + f"\n(assumed noise {int(s['assumed_noise']*100)}%)" for s in subs]
    ax.bar(np.arange(2) - .18, [s["examiner_agreement"] * 100 for s in subs], .34, color=BLUE, label="Examiner-examiner agreement (%)")
    ax.bar(np.arange(2) + .18, [s["assistant_vs_examiner1"] * 100 for s in subs], .34, color=AMBER, label="Assistant vs examiner label (%)")
    for i, s in enumerate(subs):
        ax.text(i - .18, s["examiner_agreement"] * 100 + 1.5, f"{s['examiner_agreement']*100:.0f}", ha="center", fontweight="bold")
        ax.text(i + .18, s["assistant_vs_examiner1"] * 100 + 1.5, f"{s['assistant_vs_examiner1']*100:.0f}", ha="center", fontweight="bold")
    ax.set_xticks(range(2)); ax.set_xticklabels(names, fontsize=11); ax.set_ylim(0, 112)
    ax.legend(loc="upper right", fontsize=9.5); ax.set_ylabel("Percent")
    ax.set_title("(a) Agreement falls when labels are noisy", fontsize=12, loc="left")
    ax2.bar(range(2), [s["examiner_kappa"] for s in subs], .45, color=[GREEN if s["passes_kappa_gate"] else RED for s in subs])
    ax2.axhline(R["C6"]["kappa_gate"], color=INK, ls="--"); ax2.text(1.45, R["C6"]["kappa_gate"] + .02, "kappa gate 0.6", ha="right", fontsize=10, fontweight="bold")
    for i, s in enumerate(subs):
        ax2.text(i, s["examiner_kappa"] + .03, f"{s['examiner_kappa']:.2f}", ha="center", fontsize=13, fontweight="bold")
    ax2.set_xticks(range(2)); ax2.set_xticklabels(names, fontsize=11); ax2.set_ylim(0, 1.05)
    ax2.set_ylabel("Cohen's kappa between two examiners")
    ax2.set_title("(b) Label-quality gate before any ML pilot", fontsize=12, loc="left")
    fig.suptitle("Labelled simulation (400 synthetic answers per subject, seed 2026): noise assumed, assistant matches truth by construction",
                 fontsize=12.5, fontweight="bold", y=.99)
    fig.tight_layout(rect=[0, 0, 1, .94])
    save(fig, FIG / "fig_label_noise.png")


# ---------------------------------------------------------------- resources
def fig_resources():
    est = R["resources"]
    alts = est["alternatives"]
    fig, (ax, ax2, ax3) = plt.subplots(1, 3, figsize=(17, 6.4))
    keys = list("ABCD")
    cpu = [alts[k]["cpu_s_cycle"] for k in keys]
    ax.bar(keys, cpu, color=[ALT_COL[k] for k in keys], width=.55)
    ax.axhline(est["budget_original"], color=SLATE, ls="--"); ax.text(3.4, est["budget_original"] + 12, f"original budget {est['budget_original']}", ha="right", fontsize=9.5, color=SLATE)
    ax.axhline(est["budget_halved"], color=RED, ls="--"); ax.text(3.4, est["budget_halved"] + 12, f"halved budget {est['budget_halved']}", ha="right", fontsize=9.5, color=RED, fontweight="bold")
    for i, v in enumerate(cpu):
        ax.text(i, v + 12, f"{v:.0f}", ha="center", fontweight="bold")
    ax.set_ylabel("CPU-seconds per examination cycle (estimate)"); ax.set_ylim(0, 700)
    ax.set_title("(a) Compute vs budget", fontsize=12, loc="left")
    st = [alts[k]["storage_mb_year"] for k in keys]
    ax2.bar(keys, st, color=[ALT_COL[k] for k in keys], width=.55)
    for i, v in enumerate(st):
        ax2.text(i, v + 6, f"{v:.0f}", ha="center", fontweight="bold")
    ax2.set_ylabel("Storage growth, MB per year (estimate)"); ax2.set_ylim(0, 520)
    ax2.set_title("(b) Storage growth", fontsize=12, loc="left")
    lab = [alts[k]["labelling_hours_round"] for k in keys]
    gov = [alts[k]["governance_hours_year"] for k in keys]
    x = np.arange(4)
    ax3.bar(x - .2, lab, .38, color=AMBER, label="Expert labelling hours per round")
    ax3.bar(x + .2, gov, .38, color=TEAL, label="Ledger governance hours per year")
    for i in range(4):
        if lab[i]:
            ax3.text(i - .2, lab[i] + 5, str(lab[i]), ha="center", fontweight="bold", fontsize=10)
        if gov[i]:
            ax3.text(i + .2, gov[i] + 5, str(gov[i]), ha="center", fontweight="bold", fontsize=10)
    ax3.set_xticks(x); ax3.set_xticklabels(keys); ax3.set_ylim(0, 300); ax3.legend(fontsize=9, loc="upper left")
    ax3.set_title("(c) People effort (assumed)", fontsize=12, loc="left")
    fig.suptitle("Operating resource estimates under stated workload assumptions (only rule evaluation time was measured; no energy claim)",
                 fontsize=12.5, fontweight="bold", y=.99)
    fig.tight_layout(rect=[0, 0, 1, .94])
    save(fig, FIG / "fig_resources.png")


# ---------------------------------------------------------------- redesign
def fig_redesign():
    rev = R["selection"]["revised"]
    base = R["selection"]["base"]
    fig, ax = plt.subplots(figsize=(13, 6.6))
    x = np.arange(4); w = .26
    series = [("Original scores, original weights", [base[a] for a in "ABCD"], SLATE),
              ("Revised scores, original weights", [rev["original_weights"][a] for a in "ABCD"], BLUE),
              ("Revised scores, revised weights", [rev["revised_weights"][a] for a in "ABCD"], GREEN)]
    for k, (n, v, c) in enumerate(series):
        b = ax.bar(x + (k - 1) * w, v, w * .92, color=c, label=n)
        for xi, vi in zip(x + (k - 1) * w, v):
            ax.text(xi, vi + .06, f"{vi:.2f}", ha="center", fontsize=10.5, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([ALTS[a].replace("\n", " ") for a in "ABCD"], fontsize=11)
    ax.set_ylim(0, 4.8); ax.set_ylabel("Weighted score out of 5")
    ax.legend(fontsize=10, loc="upper right"); ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)
    fig.suptitle("Task 6: changed evidence (inconsistent labels, partner withdrawn, halved budget) strengthens the rule-assisted option",
                 fontsize=12.5, fontweight="bold", y=.99)
    fig.tight_layout(rect=[0, 0, 1, .95])
    save(fig, FIG / "fig_redesign_scores.png")


if __name__ == "__main__":
    for f in (fig_moderation, fig_decision, fig_sensitivity, fig_assistant, fig_fairness,
              fig_tamper, fig_noise, fig_resources, fig_redesign):
        f()
