"""Workload-linked resource and cost estimates.

Only the rule evaluation time is MEASURED (single machine, not a benchmark).
Everything else is an explicit planning assumption/estimate and is tagged so.
"""

ASSUMPTIONS = {
    "students": 2400, "papers": 5, "answers_per_paper": 4, "cycles_per_year": 2,
    "answer_kb": 1.2, "mark_record_kb": 0.6, "audit_events_per_answer": 5, "audit_event_kb": 0.35,
    "planning_ms_per_rule_eval": 1.0,            # conservative vs measured value
    "illustrative_rs_per_vcpu_hour": 3.0,        # illustrative allocation, not a quotation
    "budget_cpu_s_per_cycle_original": 600, "budget_cpu_s_per_cycle_halved": 300,
    "ml_train_cpu_s_per_retrain": 250,           # ASSUMED, unmeasured
    "ml_infer_ms_per_answer": 3.0,               # ASSUMED, unmeasured
    "label_hours_per_subject_round": 20, "subjects": 12,   # 2 experts x 300 answers x 2 min
    "ledger_nodes": 4, "ledger_rs_per_node_month": 1500,   # ASSUMED
    "ledger_governance_hours_per_year": 48,               # ASSUMED 4 institutions x 6 meetings x 2 h
    "credentials_per_year": 800, "credential_fingerprint_kb": 1.0,
}


def estimates(measured_ms_per_eval):
    a = ASSUMPTIONS
    answers = a["students"] * a["papers"] * a["answers_per_paper"]
    rule_cpu_s = answers * a["planning_ms_per_rule_eval"] / 1000
    rule_cpu_measured_s = (answers * measured_ms_per_eval / 1000) if measured_ms_per_eval is not None else None
    ml_cpu_s = a["ml_train_cpu_s_per_retrain"] + answers * a["ml_infer_ms_per_answer"] / 1000
    per_answer_kb = a["answer_kb"] + a["mark_record_kb"] + a["audit_events_per_answer"] * a["audit_event_kb"]
    storage_cycle_mb = answers * per_answer_kb / 1024
    storage_year_mb = storage_cycle_mb * a["cycles_per_year"]
    ledger_year_cost = a["ledger_nodes"] * a["ledger_rs_per_node_month"] * 12
    ledger_storage_mb = a["credentials_per_year"] * a["credential_fingerprint_kb"] * a["ledger_nodes"] / 1024
    rs_per_cpu_s = a["illustrative_rs_per_vcpu_hour"] / 3600
    o, h = a["budget_cpu_s_per_cycle_original"], a["budget_cpu_s_per_cycle_halved"]
    alt = {
        "A": {"cpu_s_cycle": rule_cpu_s, "storage_mb_year": storage_year_mb,
              "labelling_hours_round": 0, "fixed_rs_year": 0, "governance_hours_year": 0},
        "B": {"cpu_s_cycle": rule_cpu_s + ml_cpu_s, "storage_mb_year": storage_year_mb * 1.25,
              "labelling_hours_round": a["label_hours_per_subject_round"] * a["subjects"],
              "fixed_rs_year": 0, "governance_hours_year": 0},
        "C": {"cpu_s_cycle": rule_cpu_s, "storage_mb_year": storage_year_mb + ledger_storage_mb,
              "labelling_hours_round": 0, "fixed_rs_year": ledger_year_cost,
              "governance_hours_year": a["ledger_governance_hours_per_year"]},
        "D": {"cpu_s_cycle": rule_cpu_s + ml_cpu_s,
              "storage_mb_year": storage_year_mb * 1.25 + ledger_storage_mb,
              "labelling_hours_round": a["label_hours_per_subject_round"] * a["subjects"],
              "fixed_rs_year": ledger_year_cost,
              "governance_hours_year": a["ledger_governance_hours_per_year"]},
    }
    for k, v in alt.items():
        v["compute_rs_year"] = v["cpu_s_cycle"] * a["cycles_per_year"] * rs_per_cpu_s
        v["fits_original_budget"] = v["cpu_s_cycle"] <= o
        v["fits_halved_budget"] = v["cpu_s_cycle"] <= h
    return {
        "answers_per_cycle": answers,
        "answers_per_year": answers * a["cycles_per_year"],
        "per_answer_kb": round(per_answer_kb, 3),
        "rule_cpu_s_cycle_planning": round(rule_cpu_s, 2),
        "rule_cpu_s_cycle_measured": (round(rule_cpu_measured_s, 3) if rule_cpu_measured_s is not None else None),
        "ml_cpu_s_cycle_assumed": round(ml_cpu_s, 1),
        "storage_mb_cycle": round(storage_cycle_mb, 1),
        "storage_mb_year": round(storage_year_mb, 1),
        "budget_original": o, "budget_halved": h,
        "basis": {"measured": ["rule evaluation time per answer"],
                  "estimated": ["everything else in this table"]},
        "alternatives": {k: {kk: (round(vv, 3) if isinstance(vv, float) else vv)
                             for kk, vv in v.items()} for k, v in alt.items()},
        "assumptions": a,
    }
