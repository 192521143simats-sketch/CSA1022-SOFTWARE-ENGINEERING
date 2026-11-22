# Pre-registered claims and predictions

Written **before the demonstrator was first executed**. Dataset and rubric were frozen at this point.

| File | SHA-256 |
|---|---|
| `data/synthetic_answers.csv` | `dfc1e6b5503a1419d60d259a67d1685bee20958a8a5e4dc68913ef743e17261d` |
| `data/rubric_acid.json` | `feb07d4d5243390aa2205ef6f3e23047b48bb5b12e187932888eabae6ef66247` |

Frozen at 2026-11-21T21:44:36Z (UTC). Expert bands were assigned by the author using the band definitions in `rubric_acid.json`.

## Claims (each can be falsified)

**C1 – Deterministic moderation matrix.** The stakes-discrepancy matrix (3 stakes levels x 3 discrepancy levels) reproduces all 9 defined cells and gives identical output over 1,000 repeated runs. It also never lowers priority when stakes or discrepancy rises (monotonic).
*Prediction:* 9 of 9 cells correct; 1,000 of 1,000 runs identical; 0 monotonicity violations.
*Limit:* this verifies implementation determinism, not that the cell values are the right policy.

**C2 – Abstention reduces forced wrong suggestions.** On the same 24 synthetic answers, an assistant that abstains (sends to Manual Review) on unfamiliar, negated, very short or unexplained answers makes fewer wrong suggestions than a forced-choice baseline.
*Prediction:* forced baseline makes **at least 6** wrong suggestions; the first abstaining version (v1) makes **at most 2** wrong suggestions among the answers it does suggest on.
*Design target note:* the v1 target of <= 2 is the design goal, set before running. If v1 misses it, a revision is made and the miss is reported.

**C3 – Tamper evidence of a hash-chained audit log.** A hash chain detects a naive edit, but does **not** detect (a) a privileged edit with full recomputation, or (b) truncation of the last entries, unless an external head-hash checkpoint exists; and it cannot verify that the original input was true.
*Prediction:* T1 pass; T2 detected; T3 undetected; T4 detected; T5 undetected; T5b detected; T6 chain valid (truth not checked); T7a erasing content hashed into the chain breaks the chain; T7b erasing content held outside the chain (commitment only) keeps the chain valid.

**C4 – Workflow authorisation.** The assistant cannot approve (A1); an examiner cannot approve (A3); the normal path evaluate -> moderate -> approve succeeds; an override or correction without a reason is rejected; a correction with a reason succeeds and preserves history.
*Prediction:* all workflow checks pass.

**C5 – Retry-safe credential issue.** When the external verification service is unavailable, the local mark record is preserved and the issue request is retried without creating a duplicate certificate; a tampered certificate fails verification.
*Prediction:* exactly 1 certificate after 2 simulated outages; local marks unchanged; tampered grade rejected.

**C6 – Label noise limits measurable agreement.** In a labelled simulation, a subject whose examiners have 35% label noise shows much lower examiner agreement and kappa than a subject with 5% noise, even though the rule assistant is identical.
*Prediction:* Databases kappa >= 0.7; Operating Systems kappa < 0.4. (Simulation with assumed noise, not real data.)

## Acceptance thresholds under test (planning assumptions)

- Wrong-band suggestions on answered items <= 10%.
- No suggestion may approve or publish a mark.
- Zero student identifiers in exported samples.
